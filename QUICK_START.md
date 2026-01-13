# Quick Start Guide - Dagster POC Testing

## Prerequisites Check

1. **Verify AWS Profile:**
   ```bash
   aws configure list --profile flywheel-dev
   aws sts get-caller-identity --profile flywheel-dev
   ```

2. **Install Dependencies:**
   ```bash
   cd ~/dev/acx/acx_omc_flywheel_proj
   pip install -r requirements.txt
   ```

## Start Dagster UI

```bash
cd ~/dev/acx/acx_omc_flywheel_proj
dagster dev
```

The UI will be available at: **http://localhost:3000**

## Testing Workflows

### 1. Test Monthly Refresh (Start Small)

**Option A: Test a Single Asset (Recommended First)**
1. Open Dagster UI → Assets tab
2. Find `addr_part` or `infobase_part`
3. Click "Materialize" to test one asset
4. Monitor execution in the UI

**Option B: Test Full Workflow**
1. Open Dagster UI → Jobs tab
2. Select `monthly_refresh` job
3. Click "Launch Run"
4. Monitor the complete 7-step workflow

**Option C: CLI Test (Dry Run)**
```bash
dagster asset materialize -m dagster_defs --select addr_part --dry-run
```

### 2. Test Clean Rooms Operation

**Via UI:**
1. Navigate to Jobs → `associate_tables_job`
2. Click "Launch Run"
3. Configure:
   ```json
   {
     "ops": {
       "associate_tables_to_collaboration": {
         "config": {
           "membership_id": "your-membership-id-here"
         }
       }
     }
   }
   ```
4. Launch and monitor

**Via CLI:**
```bash
dagster job execute -m dagster_defs -j associate_tables_job \
  --config '{"ops": {"associate_tables_to_collaboration": {"config": {"membership_id": "your-membership-id"}}}}'
```

## Verification Checklist

- [ ] Dagster UI starts without errors
- [ ] All 8 assets visible in Assets tab
- [ ] AWS credentials working (check logs for "AWS clients initialized")
- [ ] Can materialize a single asset successfully
- [ ] Asset dependencies are correct (check DAG visualization)
- [ ] Glue jobs execute correctly
- [ ] Clean Rooms operation works

## Troubleshooting

### Import Errors
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
dagster dev
```

### AWS Authentication Issues
- Verify profile: `aws configure list --profile flywheel-dev`
- Test credentials: `aws sts get-caller-identity --profile flywheel-dev`

### Glue Job Not Found
- Verify job names match in `dagster_defs/__init__.py`
- Check job exists: `aws glue get-job --job-name etl-omc-flywheel-dev-addressable-split-and-part --profile flywheel-dev`

### Module Not Found
- Ensure you're in project root: `cd ~/dev/acx/acx_omc_flywheel_proj`
- Check Python path includes current directory

## Next Steps After Testing

1. **Validate Asset Dependencies**: Ensure the DAG flows correctly
2. **Test Parallel Execution**: Verify steps 1A/1B and 5A/5B run in parallel
3. **Test Error Handling**: Intentionally fail a job to see retry behavior
4. **Test Re-execution**: Re-materialize a single asset to verify skip-steps equivalent
5. **Compare with Step Functions**: Run same workflow in both systems and compare

## Current Configuration

- **Profile**: `flywheel-dev`
- **Region**: `us-east-1`
- **Environment**: `dev`
- **Database**: `omc_flywheel_dev_clean`
- **S3 Paths**: 
  - Addressable: `s3://omc-flywheel-data-us-east-1-dev/omc_cleanroom_data/split_part/addressable_ids/`
  - Infobase: `s3://omc-flywheel-data-us-east-1-dev/omc_cleanroom_data/split_part/infobase_attributes/`

All configuration is in `dagster_defs/__init__.py` and can be modified there.

