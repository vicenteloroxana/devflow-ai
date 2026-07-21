variable "aws_region" {
  description = "Región de AWS donde se despliega la infraestructura"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Nombre del ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
}
