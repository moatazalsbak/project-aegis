# 🛡️ Project Aegis: The Self-Driving Cost Optimizer for AWS

Project Aegis is an intelligent AWS cost optimization system that automatically discovers, validates, and implements cost-saving opportunities across your infrastructure. Think of it as your tireless DevOps engineer who never sleeps, constantly finding ways to reduce your AWS bill while maintaining performance and reliability.

## 🎯 What Does It Do?

Aegis automates the entire cost optimization lifecycle:
- **Discovers** optimization opportunities using AWS Compute Optimizer and custom analysis
- **Validates** each opportunity against your requirements and risk tolerance
- **Implements** approved changes safely using Infrastructure as Code
- **Monitors** the results and rolls back if issues are detected
- **Reports** your savings and system health in real-time

### Quick Wins Aegis Targets

- Unused or underutilized resources (EBS volumes, Elastic IPs, idle load balancers)
- Oversized EC2 instances that can be downsized
- x86 instances that can migrate to cost-effective Graviton processors
- Inefficient Lambda configurations
- Unattached resources accumulating charges

### 🎁 Benefits for Your Team

✅ **Easy Setup** – Get started in minutes with minimal configuration  
✅ **Ongoing Savings** – Continuous optimization without manual effort  
✅ **No Performance Loss** – Smart automation protects reliability and speed  
✅ **Full Visibility** – Track every change and savings achieved  
✅ **Peace of Mind** – Safe, gradual rollouts with automatic rollback

### 👥 Who is Project Aegis For?

Perfect for:

- 🔧 **DevOps Engineers** looking to automate cost management
- ☁️ **Cloud Engineers** responsible for AWS spend optimization
- 🏗️ **Platform Teams** managing infrastructure at scale
- 💼 **Engineering Leaders** wanting to reduce cloud costs without adding headcount

### 🔄 How It Works – A Quick Example

1. **Discovery** – Aegis scans your AWS account and finds 20 EC2 instances that could save 40% by switching to Graviton processors
2. **Validation** – Aegis checks compatibility, performance requirements, and risk factors
3. **Approval** – Based on your policies, Aegis auto-approves low-risk changes or requests your review
4. **Implementation** – Aegis generates Terraform code and applies the changes gradually
5. **Monitoring** – Aegis watches for any issues and can roll back automatically if needed
6. **Reporting** – You see the savings in your dashboard: $1,200/month saved! 🎉

---

## 🚀 Installation & Getting Started

### Prerequisites

Before you begin, make sure you have:

- An AWS account with appropriate permissions
- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- [Terraform](https://www.terraform.io/downloads.html) (version 1.0 or later)
- [Python 3.9+](https://www.python.org/downloads/) installed
- Git installed on your machine

### Step 1: Clone the Repository

```bash
git clone https://github.com/moatazalsbak/project-aegis.git
cd project-aegis
```

### Step 2: Configure AWS Credentials

Ensure your AWS CLI is configured with credentials that have the necessary permissions:

```bash
aws configure
```

You'll need permissions for:
- EC2, Lambda, and other compute services
- AWS Compute Optimizer
- CloudWatch for monitoring
- IAM for creating service roles

### Step 3: Set Up the Infrastructure

Navigate to the Terraform directory and initialize:

```bash
cd terraform
terraform init
```

Review the planned changes:

```bash
terraform plan
```

Apply the infrastructure:

```bash
terraform apply
```

Type `yes` when prompted to confirm.

### Step 4: Deploy the Lambda Function

The Lambda function is automatically deployed via Terraform. Once the apply completes, you'll see output with the Lambda function ARN and other key resources.

### Step 5: Verify the Setup

Check that everything is running:

```bash
aws lambda list-functions --query 'Functions[?contains(FunctionName, `aegis`)].FunctionName'
```

You should see your Aegis Lambda function listed.

---

## 📖 Usage Instructions

### Running the Optimizer

Aegis runs automatically on a schedule (configured in Terraform), but you can also trigger it manually:

#### Manual Invocation via AWS CLI

```bash
aws lambda invoke \
  --function-name aegis-discovery-engine \
  --payload '{}' \
  response.json

cat response.json
```

#### Manual Invocation via AWS Console

1. Navigate to the AWS Lambda console
2. Find the `aegis-discovery-engine` function
3. Click "Test" and create a new test event with an empty payload `{}`
4. Click "Test" to run the function

### Understanding the Output

The optimizer will:

1. **Scan your AWS account** for optimization opportunities
2. **Log findings** to CloudWatch Logs
3. **Generate recommendations** for cost savings
4. **Create Terraform code** for approved changes (if auto-approve is enabled)
5. **Report metrics** to CloudWatch for tracking

### Monitoring and Logs

View the optimizer's activity:

```bash
aws logs tail /aws/lambda/aegis-discovery-engine --follow
```

Or check CloudWatch Logs in the AWS Console under:
- Log Group: `/aws/lambda/aegis-discovery-engine`

### Expected Outcomes

After running Aegis, you should see:

- **Detailed cost optimization recommendations** in the logs
- **Potential monthly savings** calculated for each opportunity
- **Risk assessment** for each recommended change
- **Generated Terraform code** (in your configured output location) for safe implementation

### Sample Configuration

While Aegis works with sensible defaults, you can customise behaviour by modifying the Lambda environment variables in your Terraform configuration:

```hcl
environment {
  variables = {
    AUTO_APPROVE_THRESHOLD = "100"  # Auto-approve changes under $100/month impact
    RISK_TOLERANCE        = "low"   # Options: low, medium, high
    DRY_RUN_MODE         = "false" # Set to true to prevent any actual changes
  }
}
```

---

## 🤝 Contributing

We welcome contributions from the community! Whether it's fixing a bug, adding a feature, or improving documentation, your help makes Aegis better for everyone.

### How to Contribute

1. **Fork the repository** to your own GitHub account
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/project-aegis.git
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-awesome-feature
   ```
4. **Make your changes** and commit them with clear messages:
   ```bash
   git commit -m "Add support for RDS instance optimization"
   ```
5. **Push to your fork**:
   ```bash
   git push origin feature/your-awesome-feature
   ```
6. **Open a Pull Request** on the main repository

### Areas We'd Love Help With

- 🐛 **Bug fixes** – Found something broken? Fix it and send a PR!
- ✨ **New optimization strategies** – Add support for more AWS services
- 📚 **Documentation improvements** – Make the docs clearer and more comprehensive
- 🧪 **Testing** – Add unit tests, integration tests, or test coverage
- 🎨 **UI/Reporting enhancements** – Improve how savings are visualized

### Reporting Issues

Found a bug or have a feature request? [Open an issue](https://github.com/moatazalsbak/project-aegis/issues) on GitHub. Please include:

- Clear description of the problem or feature
- Steps to reproduce (for bugs)
- Expected vs actual behaviour
- Your environment details (AWS region, Terraform version, etc.)

### Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Include tests for new functionality
- Update documentation as needed
- Follow the existing code style
- Write clear commit messages

For more details, check out our [Issues](https://github.com/moatazalsbak/project-aegis/issues) and [Pull Requests](https://github.com/moatazalsbak/project-aegis/pulls) tabs to see what's currently in progress.

---

## 💬 Support & Contact

Need help or have questions? We're here for you!

### Get Help

- 🐛 **Found a bug?** [Open an issue](https://github.com/moatazalsbak/project-aegis/issues) on GitHub
- 💡 **Feature request?** [Create a feature request](https://github.com/moatazalsbak/project-aegis/issues/new) issue
- 📖 **Need guidance?** Check the README sections above for setup and usage instructions

### Community

Join other Aegis users:

- 💬 **Ask questions** via [GitHub Issues](https://github.com/moatazalsbak/project-aegis/issues)
- 🔧 **Contribute code** via [Pull Requests](https://github.com/moatazalsbak/project-aegis/pulls)
- ⭐ **Star the repo** if you find it useful!

We aim to respond to issues and PRs within 48 hours. Your feedback helps make Aegis better for everyone!

---

## 📄 License

License details coming soon.

---

## 🌟 Acknowledgments

- AWS Compute Optimizer team for the excellent API
- [AWS Lambda Power Tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning) by Alex Casalboni

---

**Made with ❤️ for the AWS community**
