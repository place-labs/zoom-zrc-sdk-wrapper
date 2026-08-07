# EKS stable-MAC node — setup & verification

Why this exists: the Zoom SDK derives its credential-encryption key from the
host's real `eth0` MAC. To make pairings survive pod recreation, the workload
runs with `hostNetwork: true` on a **dedicated self-managed node whose primary
ENI (and therefore MAC) is stable**. See ARCHITECTURE.md (deployment topology)
and FINDINGS.md §2–4 for the reasoning; `deploy/k8s/zoom-zrc.yaml` for the
workload.

> **Source-of-truth note.** The sections marked **VERIFIED** are facts from the
> AWS colleague's handoff, confirmed against the live cluster. The section marked
> **RECONSTRUCTED** infers the commands that would produce this end-state — it is
> **not** a record of what was actually run. Replace it with the colleague's
> actual IaC (`eksctl` config / Terraform / CLI history); that is the only
> authoritative, reproducible source for the exact commands.

## VERIFIED — infrastructure facts (from handoff, confirmed live)

| Item | Value |
|---|---|
| Cluster | `PlaceOS-NonProd-Cluster-IPv4` (region `us-west-2`) |
| Node — EC2 Name tag | `avits-services-self-managed-node` |
| Node — Kubernetes object | `ip-10-80-24-89.us-west-2.compute.internal` |
| Node — friendly label | `avit.ucla.edu/node-name=avits-services-self-managed-node` |
| Node subnet | `subnet-08e79139f40c6a897` · `10.80.24.0/24` · `us-west-2a` |
| **Primary ENI MAC (stable)** | **`02:ff:cb:fe:09:a3`** — confirmed via `ip link show eth0` in-pod |
| EKS cluster security group | `sg-0cb75d0666d52fb72` |
| Dedicated node security group | `sg-0de4a163323f5f310` |
| StorageClass | `avits-services-self-managed-ebs` |
| Pod networking | Node network namespace (`hostNetwork`); IP + SDK-visible MAC from the node's **retained primary ENI** in the standard EKS node subnet. No separate Pod subnet, no ENIConfig. |

## VERIFIED — workload contract (from handoff)

The pod **must** carry these, or the stable-MAC guarantee breaks (already encoded
in `deploy/k8s/zoom-zrc.yaml`):

```yaml
spec:
  nodeSelector:
    avit.ucla.edu/node-pool: avits-services-self-managed
    avit.ucla.edu/node-network: eks-standard
  tolerations:
    - key: avit.ucla.edu/dedicated
      operator: Equal
      value: avits-services-self-managed
      effect: NoSchedule
  hostNetwork: true                 # SDK must see the node's real eth0, not a per-pod CNI MAC
  dnsPolicy: ClusterFirstWithHostNet
```

- One replica (StatefulSet, or Deployment with `Recreate`) — never overlap old
  and new pods (two SDK instances collide on device identity *and*, with host
  networking, on the port).
- Declare every listening `containerPort` — with host networking it binds the
  node's port and must not conflict.
- Do **not** add a fixed-MAC helper, `NET_ADMIN`, privileged mode, or interface
  modification — the persistent ENI supplies the stable MAC.

## RECONSTRUCTED — how the node was likely prepared  ⚠ verify against colleague's IaC

> These are inferred steps to reproduce the VERIFIED end-state above, not the
> actual commands. Items in `<angle brackets>` are unknowns to obtain from the
> colleague. Prefer replacing this whole section with their `eksctl`/Terraform.

The end-state is a **self-managed EKS node** (not a managed node group — implied
by the `self-managed` naming and the taint/label scheme) with a **stable primary
ENI**. Reproducing it involves:

1. **A stable primary ENI.** A MAC that survives instance stop/start *and*
   replacement means the ENI is decoupled from the instance lifecycle — i.e.
   pre-created and attached at `DeviceIndex=0`, not the ephemeral instance-default
   ENI. (Stop/start alone retains the ENI; termination destroys a default one.)
   ```bash
   # Pre-create the ENI in the node subnet with the dedicated node SG:
   aws ec2 create-network-interface \
     --subnet-id subnet-08e79139f40c6a897 \
     --groups sg-0de4a163323f5f310 sg-0cb75d0666d52fb72 \
     --description "zrc stable-MAC primary ENI" --region us-west-2
   #  → note the ENI id and its MAC (should be 02:ff:cb:fe:09:a3 if this is that ENI)
   ```
   *(If instead they rely on stop/start of a normal instance, the MAC is stable
   only until the instance is terminated — confirm which model is in use.)*

2. **Launch the EC2 instance as a self-managed node**, attaching that ENI as
   eth0, in `us-west-2a`, running the EKS-optimized AMI, and joining the cluster
   via the bootstrap script with the taint + labels baked into kubelet args:
   ```bash
   aws ec2 run-instances --region us-west-2 \
     --image-id <eks-optimized-ami-for-cluster-k8s-version> \
     --instance-type <instance-type> \
     --iam-instance-profile Name=<eks-node-instance-profile> \
     --network-interfaces "NetworkInterfaceId=<eni-id-from-step-1>,DeviceIndex=0" \
     --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=avits-services-self-managed-node}]' \
     --user-data '<base64 or file:// of the bootstrap userdata, see below>'
   ```
   Bootstrap userdata (self-managed node join + taint/labels):
   ```bash
   #!/bin/bash
   /etc/eks/bootstrap.sh PlaceOS-NonProd-Cluster-IPv4 \
     --kubelet-extra-args '--node-labels=avit.ucla.edu/node-pool=avits-services-self-managed,avit.ucla.edu/node-network=eks-standard,avit.ucla.edu/node-name=avits-services-self-managed-node --register-with-taints=avit.ucla.edu/dedicated=avits-services-self-managed:NoSchedule'
   ```

3. **Authorize the node's IAM role to join** (self-managed nodes need this in the
   `aws-auth` ConfigMap; managed groups do it automatically):
   ```bash
   eksctl create iamidentitymapping --cluster PlaceOS-NonProd-Cluster-IPv4 --region us-west-2 \
     --arn <node-instance-role-arn> --group system:bootstrappers --group system:nodes \
     --username system:node:{{EC2PrivateDNSName}}
   # (or edit the aws-auth ConfigMap directly)
   ```

4. **StorageClass** for the pod's PVC:
   ```yaml
   # kubectl apply -f -
   apiVersion: storage.k8s.io/v1
   kind: StorageClass
   metadata:
     name: avits-services-self-managed-ebs
   provisioner: ebs.csi.aws.com
   volumeBindingMode: WaitForFirstConsumer   # bind in the node's AZ (us-west-2a)
   parameters:
     type: gp3
   ```
   *(Provisioner/parameters/`allowedTopologies` unconfirmed — get from colleague.)*

**Unknowns to fill from the colleague's actual setup:** launch mechanism
(`eksctl` self-managed nodegroup vs raw `run-instances` vs Terraform), AMI id,
instance type, node IAM role ARN, the exact ENI model (pre-created vs
stop/start-retained), and the StorageClass provisioner/parameters.

## VERIFIED — post-setup verification (run before pairing rooms)

Confirmed working on 2026-08-07 (K8s node) and reproduced locally:

```bash
# 1. the SDK must see the stable ENI MAC
kubectl -n placeos exec zoom-zrc-0 -- cat /sys/class/net/eth0/address
#    → must print 02:ff:cb:fe:09:a3   (eth1 also exists — that's the VPC CNI, ignore)

# 2. pair ONE test room, then prove persistence across pod recreation:
kubectl -n placeos delete pod zoom-zrc-0
kubectl -n placeos get pods -w                       # wait 1/1 Running
kubectl -n placeos logs zoom-zrc-0 | grep -i RetryToPairRoom
#    → "RetryToPairRoom result: ZRCSDKERR_SUCCESS"  = credentials survived (MAC held)
#    → "...INTERNAL_ERROR"                            = MAC changed; STOP, do not pair the fleet
```

Only after step 2 passes, pair the remaining rooms.
