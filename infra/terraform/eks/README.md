# AWS EKS scaffold

This folder is an opt-in infrastructure starting point, not an automatic deployment. Review costs, quotas, CIDRs, access policy, region, and organizational guardrails before applying.

## Prerequisites

- Terraform >= 1.6
- AWS CLI authenticated to a dedicated sandbox account
- Permissions reviewed for VPC, EKS, IAM, and EC2 resources

## Usage

```bash
cd infra/terraform/eks
cp terraform.tfvars.example terraform.tfvars
# Edit region, cluster name, and VPC CIDR.
terraform init
terraform fmt -check
terraform validate
terraform plan
# Apply only after reviewing the plan and expected cost.
```

The module creates an EKS cluster and managed node group using the upstream `terraform-aws-modules/eks/aws` module. It is intentionally not connected to CI auto-apply. Delete the sandbox resources when finished.

For a production account, additionally design private endpoint access, egress, workload identity, secrets encryption, cluster logging, backup/restore, network policy, upgrade policy, quotas, budgets, and incident response. Do not treat this scaffold as a complete production landing zone.
