provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "devflow-ai"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
