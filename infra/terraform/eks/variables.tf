variable "aws_region" {
  description = "AWS region for the sandbox EKS cluster."
  type        = string
  default     = "ap-south-1"
}

variable "cluster_name" {
  description = "Name for the EKS cluster."
  type        = string
  default     = "agentops-sandbox"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version supported by the selected AWS region."
  type        = string
  default     = "1.33"
}

variable "vpc_id" {
  description = "Existing VPC ID. This scaffold does not create a VPC."
  type        = string
}

variable "subnet_ids" {
  description = "At least two subnet IDs in distinct AZs in the selected VPC."
  type        = list(string)
  validation {
    condition     = length(var.subnet_ids) >= 2
    error_message = "Provide at least two subnet IDs in distinct Availability Zones."
  }
}

variable "cluster_endpoint_public_access" {
  description = "Whether the EKS API endpoint is publicly reachable. Restrict CIDRs before production."
  type        = bool
  default     = false
}

variable "node_instance_types" {
  description = "EC2 instance types for the managed node group."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_min_size" {
  type    = number
  default = 1
}

variable "node_max_size" {
  type    = number
  default = 3
}

variable "node_desired_size" {
  type    = number
  default = 1
}

variable "environment" {
  type    = string
  default = "sandbox"
}
