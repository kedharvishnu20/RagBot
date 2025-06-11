# Project Maintenance Guide

## 🧹 Regular Maintenance Tasks

### Daily Operations

#### Using the Cleanup Script

The project includes an automated cleanup script for regular maintenance:

```bash
# Run the cleanup script
cleanup.bat

# Or manually clean specific items
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
```

#### What the Cleanup Script Does:

- Removes Python cache directories (`__pycache__/`)
- Deletes compiled Python files (`.pyc`)
- Removes temporary files (`.tmp`, `.temp`, `*~`)
- Cleans log files (`.log`)
- Removes test files from study_docs
- Deletes backup database files

### Weekly Maintenance

#### 1. Database Cleanup

```bash
# Check database size
dir rag_app.db

# Optional: Vacuum database to reclaim space
python -c "import sqlite3; conn=sqlite3.connect('rag_app.db'); conn.execute('VACUUM'); conn.close()"
```

#### 2. Vector Store Optimization

```bash
# Check vector store size
dir vector_store\

# If index becomes too large, consider rebuilding
# This will recreate the index from current documents
# Access via web interface: "Rebuild Index" button
```

#### 3. Converted PDFs Management

```bash
# Check converted PDFs directory size
dir converted_pdfs\

# Optional: Clear old conversions (they will be regenerated as needed)
# del converted_pdfs\*.pdf
```

### Monthly Maintenance

#### 1. Dependency Updates

```bash
# Check for outdated packages
pip list --outdated

# Update specific packages (be careful with major versions)
pip install --upgrade fastapi uvicorn

# For safety, test after updates
python serializable_server.py --test-mode
```

#### 2. Log Analysis

```bash
# If you enable logging, analyze log files
# Look for patterns in errors or performance issues
# Consider log rotation if files become large
```

#### 3. Performance Monitoring

- Monitor response times for document preview
- Check conversion cache hit rates
- Analyze API key usage patterns
- Review database query performance

## 🚨 Troubleshooting Maintenance

### Common Cleanup Issues

#### 1. Permission Errors

```bash
# If cleanup.bat fails with permission errors
# Run as administrator or check file permissions
icacls . /grant %USERNAME%:F /T
```

#### 2. Large Cache Directories

```bash
# If __pycache__ directories are very large
# Check for runaway processes or memory leaks
# Consider system restart if issues persist
```

#### 3. Database Lock Issues

```bash
# If database appears locked during maintenance
# Check for running application instances
tasklist | findstr python

# Kill if necessary
taskkill /IM python.exe /F
```

### Conversion Cache Management

#### When to Clear Conversion Cache

- After updating conversion libraries
- If converted PDFs appear corrupted
- When storage space is low
- After changing conversion settings

#### How to Clear Conversion Cache

```bash
# Clear all converted PDFs
del converted_pdfs\*.pdf

# Or clear specific file conversions
del converted_pdfs\*specific_filename*.pdf
```

## 📊 Monitoring and Metrics

### Performance Indicators

#### 1. File Conversion Success Rate

- Monitor conversion failures in logs
- Track fallback method usage
- Identify problematic document types

#### 2. API Usage Patterns

- Track API key rotation frequency
- Monitor quota consumption
- Identify peak usage periods

#### 3. Storage Growth

- Monitor study_docs directory size
- Track converted_pdfs growth
- Watch vector_store expansion

### Health Checks

#### Daily Health Check Script

```bash
@echo off
echo === RAG AI App Health Check ===

echo Checking server accessibility...
curl -s http://localhost:8000/api/system/health > nul
if %errorlevel% equ 0 (
    echo ✓ Server is responding
) else (
    echo ✗ Server is not accessible
)

echo Checking database...
if exist rag_app.db (
    echo ✓ Database file exists
) else (
    echo ✗ Database file missing
)

echo Checking vector store...
if exist vector_store\index.faiss (
    echo ✓ Vector index exists
) else (
    echo ✗ Vector index missing
)

echo Checking dependencies...
python -c "import fastapi, uvicorn, docx2pdf; print('✓ Core dependencies OK')" 2>nul
if %errorlevel% neq 0 (
    echo ✗ Missing dependencies
)

echo === Health Check Complete ===
```

## 🔄 Backup and Recovery

### What to Backup

#### Essential Files:

- `rag_app.db` - Main database
- `.env` - Configuration (without committing API keys)
- `study_docs/` - Uploaded documents
- `vector_store/` - Generated embeddings

#### Optional Files:

- `converted_pdfs/` - Can be regenerated
- Log files - For debugging history

### Backup Script

```bash
@echo off
set BACKUP_DIR=backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%

echo Creating backup directory: %BACKUP_DIR%
mkdir %BACKUP_DIR%

echo Backing up database...
copy rag_app.db %BACKUP_DIR%\

echo Backing up documents...
xcopy study_docs %BACKUP_DIR%\study_docs\ /E /I

echo Backing up vector store...
xcopy vector_store %BACKUP_DIR%\vector_store\ /E /I

echo Backup complete: %BACKUP_DIR%
```

### Recovery Procedures

#### Database Recovery:

1. Stop the application
2. Replace `rag_app.db` with backup
3. Restart application
4. Verify data integrity

#### Document Recovery:

1. Replace `study_docs/` with backup
2. Rebuild vector index via web interface
3. Test document preview functionality

#### Vector Store Recovery:

1. Replace `vector_store/` with backup
2. Or rebuild from documents if backup unavailable
3. Test search functionality

## 🔧 Advanced Maintenance

### Performance Optimization

#### 1. Database Optimization

```sql
-- Run periodically to optimize database
PRAGMA optimize;
PRAGMA wal_checkpoint(TRUNCATE);
```

#### 2. Vector Store Optimization

- Consider periodic index rebuilding for large document sets
- Monitor embedding quality and update models if needed
- Optimize chunk sizes based on document types

#### 3. Conversion Optimization

- Monitor conversion method success rates
- Update conversion libraries regularly
- Consider preprocessing documents for better conversion

### Security Maintenance

#### 1. API Key Rotation

- Regularly rotate Google API keys
- Monitor usage quotas and costs
- Update environment variables securely

#### 2. File Security

- Regular virus scans of uploaded documents
- Monitor for suspicious file uploads
- Implement file type validation

#### 3. Access Control

- Review application access logs
- Monitor for unusual usage patterns
- Consider implementing user authentication

## 📋 Maintenance Schedule Template

### Daily (Automated via cleanup.bat):

- [ ] Run cleanup script
- [ ] Check server health
- [ ] Monitor error logs

### Weekly:

- [ ] Review conversion success rates
- [ ] Check storage usage
- [ ] Analyze performance metrics
- [ ] Test backup procedures

### Monthly:

- [ ] Update dependencies (test first)
- [ ] Optimize database
- [ ] Review security measures
- [ ] Document any issues or improvements

### Quarterly:

- [ ] Full system backup
- [ ] Performance review and optimization
- [ ] Update documentation
- [ ] Plan for future improvements

This maintenance guide ensures your RAG AI application continues to run smoothly and efficiently over time.
