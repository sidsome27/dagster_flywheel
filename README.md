# OMC Flywheel Clean Rooms - Dagster POC

This is a proof-of-concept implementation of the OMC Flywheel database refresh and Clean Rooms collaboration management workflows using Dagster.

## Overview

This Dagster project replaces AWS Step Functions for orchestrating:
1. **Monthly Refresh Workflow** - 8-asset pipeline for refreshing partitioned tables
2. **Ad-hoc Clean Rooms Operations** - Collaboration and table association management

## Project Structure

```
dagster_defs/
├── assets/
│   ├── monthly_refresh/      # Monthly refresh assets (8 assets)
│   │   ├── split_jobs.py
│   │   ├── register_tables.py
│   │   ├── prepare_tables.py
│   │   ├── er_table.py
│   │   └── reports.py
│   └── cleanrooms/           # Clean Rooms assets (future)
├── ops/
│   └── cleanrooms/           # Ad-hoc CR operations
│       └── associations.py
├── resources/                # AWS clients and configuration
│   ├── aws.py
│   └── config.py
├── jobs/                      # Job definitions
│   ├── monthly_refresh_job.py
│   └── cleanrooms_jobs.py
├── config/                    # Environment configs
│   └── dev.yaml
└── __init__.py                # Main definitions
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

Ensure your AWS credentials are configured for the `flywheel-dev` profile:

```bash
aws configure --profile flywheel-dev
```

### 3. Start Dagster UI

```bash
dagster dev
```

This will start the Dagster UI at `http://localhost:3000`

## Usage

### Monthly Refresh Workflow

The monthly refresh workflow consists of 8 assets representing independently meaningful outputs:

**Data Assets:**
1. **addr_part** - Partitioned addressable IDs dataset
2. **infobase_part** - Partitioned infobase attributes dataset
3. **addr_glue_reg** - Addressable IDs tables registered in Glue catalog
4. **infobase_glue_reg** - Infobase attributes tables registered in Glue catalog
5. **glue_ready** - Query-ready state (tables + partitions repaired and validated)
6. **er_table** - Entity Resolution table

**Artifact Assets:**
7. **data_monitor_rpt** - Data Monitor report artifact
8. **cr_rpt** - Cleanrooms report artifact

We model 8 assets because there are 8 independently meaningful outputs (two partitioned datasets, two registered-catalog states, one query-ready state, one ER table, and two reporting artifacts). Parallelization is a runtime detail that affects execution, not the asset model.

**Run via UI:**
1. Open Dagster UI
2. Navigate to "Assets" tab
3. Select assets to materialize
4. Click "Materialize"

**Run via CLI:**
```bash
dagster asset materialize -m dagster_defs --select monthly_refresh
```

**Scheduled Execution:**
The workflow is scheduled to run monthly on the 1st at 2 AM UTC via the `monthly_refresh_schedule`.

### Clean Rooms Operations

#### Associate Tables to Collaboration

Associate configured tables with a Clean Rooms collaboration membership.

**Via UI:**
1. Navigate to "Jobs" tab
2. Select "associate_tables_job"
3. Configure:
   - `membership_id`: Clean Rooms membership ID
   - `table_prefix`: Table prefix to match (default: "part_")
   - `exclude_tables`: Tables to exclude (default: ["n_a", "n_a_a"])
   - `role_name`: IAM role name (default: "cleanrooms-glue-s3-access")
   - `max_associations`: Max associations (default: 25)

**Via CLI:**
```bash
dagster job execute -m dagster_defs -j associate_tables_job \
  --config '{"ops": {"associate_tables_to_collaboration": {"config": {"membership_id": "your-membership-id"}}}}'
```

## Configuration

### Environment Configuration

Resources are configured in `dagster_defs/__init__.py` with environment-aware defaults. The environment is determined by the `DAGSTER_ENV` environment variable (defaults to `dev`).

**Development:**
- Uses hardcoded dev values
- AWS profile: `flywheel-dev`
- All config values are in code

**Production:**
- Uses environment variables for all configurable values
- AWS credentials come from IAM role (no profile needed)
- Set `DAGSTER_ENV=prod` to use production configuration

### Production Setup

To avoid "missing config" prompts in production:

1. **Set Environment Variable:**
   ```bash
   export DAGSTER_ENV=prod
   ```

2. **Configure Environment Variables (optional, defaults provided):**
   ```bash
   export AWS_REGION=us-east-1
   export DATABASE_NAME=omc_flywheel_prod_clean
   export S3_ROOT_ADDRESSABLE=s3://omc-flywheel-data-us-east-1-prod/...
   export S3_ROOT_INFOBASE=s3://omc-flywheel-data-us-east-1-prod/...
   export ROLE_NAME=cleanrooms-glue-s3-access
   export SNS_TOPIC_ARN=arn:aws:sns:...
   ```

3. **AWS Credentials:**
   - In production, use IAM roles (no AWS profile needed)
   - The code automatically uses IAM role when `aws_profile` is `None`
   - Set `AWS_PROFILE` env var only if you need to override

4. **Why No Config Prompt:**
   - All `ConfigurableResource` fields have default values or are provided in code
   - Resources are defined in `Definitions`, so they're always available
   - The "scaffold missing config" UI feature is optional - clicking it generates an empty config since everything is already provided

### Config Files

Config files in `dagster_defs/config/` serve as documentation and can be used for local testing:
- `dev.yaml` - Development configuration
- `prod.yaml` - Production configuration template

These files are not automatically loaded but can be referenced when using Dagster's config system.

## Development

### Running Tests

```bash
# Run asset tests
dagster asset materialize -m dagster_defs --select addr_part --dry-run

# Test individual ops
dagster job execute -m dagster_defs -j associate_tables_job --dry-run
```

### Adding New Assets

1. Create asset file in `dagster_defs/assets/monthly_refresh/`
2. Define asset with dependencies
3. Import in `dagster_defs/assets/monthly_refresh/__init__.py`
4. Add to `defs` in `dagster_defs/__init__.py`

### Adding New Operations

1. Create op file in `dagster_defs/ops/cleanrooms/`
2. Define op with Config schema
3. Create job in `dagster_defs/jobs/cleanrooms_jobs.py`
4. Add job to `defs` in `dagster_defs/__init__.py`

## Migration from Step Functions

### Key Differences

1. **Python vs JSON**: Dagster uses Python code instead of JSON state machine definitions
2. **Dependencies**: Asset dependencies are explicit in code, not inferred from execution order
3. **Re-execution**: Can re-materialize any asset independently (like `--skip-steps`)
4. **Observability**: Built-in UI with asset lineage and materialization history

### Migration Checklist

- [x] Monthly refresh assets (8 assets)
- [x] Basic CR operation (associate tables)
- [ ] Additional CR operations (ML config, providers, etc.)
- [ ] SNS notifications integration
- [ ] Error handling and retries
- [ ] Production configuration
- [ ] Monitoring and alerting

## Troubleshooting

### AWS Authentication Issues

If you see authentication errors:
1. Verify AWS profile: `aws configure list --profile flywheel-dev`
2. Check credentials: `aws sts get-caller-identity --profile flywheel-dev`

### Glue Job Failures

Check CloudWatch logs for the specific Glue job:
```bash
aws logs tail /aws-glue/jobs/output --follow --profile flywheel-dev
```

### Import Errors

Ensure you're in the project root and Dagster can find the module:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Next Steps

1. **Test Monthly Refresh**: Run a complete monthly refresh workflow in dev
2. **Add More CR Ops**: Implement ML configuration, provider updates, etc.
3. **Add Notifications**: Integrate SNS notifications for job completion
4. **Production Setup**: Configure for production environment
5. **Documentation**: Expand documentation as features are added

## Resources

- [Dagster Documentation](https://docs.dagster.io/)
- [Dagster AWS Integration](https://docs.dagster.io/integrations/aws)
- [Dagster Concepts](https://docs.dagster.io/concepts)

