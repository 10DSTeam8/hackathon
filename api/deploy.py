#!/usr/bin/env python3
"""
AWS Lambda Deployment Script for Flask API

This script packages the Flask Lambda API into a deployment-ready zip file
that can be directly uploaded to AWS Lambda.

Usage:
    python deploy.py

The script will:
1. Create a temporary build directory
2. Install production dependencies
3. Copy application files
4. Create a zip file ready for Lambda deployment
"""

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
import tempfile


def run_command(command, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e}")
        print(f"Error output: {e.stderr}")
        raise


def install_dependencies(target_dir):
    """Install production dependencies using pipenv."""
    print("Installing production dependencies...")
    
    # Install dependencies using pipenv
    run_command(f"pipenv requirements > requirements.txt")
    run_command(f"pip install -r requirements.txt -t {target_dir}")
    
    # Clean up temporary requirements file
    if os.path.exists("requirements.txt"):
        os.remove("requirements.txt")


def copy_application_files(source_dir, target_dir):
    """Copy application files to the target directory."""
    print("Copying application files...")
    
    # Files to include in the deployment package
    files_to_include = [
        'main.py'
    ]
    
    for file_name in files_to_include:
        source_file = os.path.join(source_dir, file_name)
        target_file = os.path.join(target_dir, file_name)
        
        if os.path.exists(source_file):
            shutil.copy2(source_file, target_file)
            print(f"  Copied: {file_name}")
        else:
            print(f"  Warning: {file_name} not found")


def create_zip_package(build_dir, output_file):
    """Create a zip file from the build directory."""
    print(f"Creating deployment package: {output_file}")
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate the archive path relative to build_dir
                archive_path = os.path.relpath(file_path, build_dir)
                zipf.write(file_path, archive_path)
                
    print(f"  Package size: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")


def clean_package_directory(build_dir):
    """Clean up unnecessary files from the package directory."""
    print("Cleaning up package directory...")
    
    # Directories and files to remove
    cleanup_patterns = [
        '**/__pycache__',
        '**/*.pyc',
        '**/*.pyo',
        '**/*.dist-info',
        '**/*.egg-info',
        '**/tests',
        '**/test',
        '**/examples',
        '**/*.md',
        '**/LICENSE*',
        '**/NOTICE*',
        '**/README*',
        # Remove specific packages that are not needed in Lambda
        '**/pip',
        '**/pip-*',
        '**/setuptools',
        '**/setuptools-*',
        '**/wheel',
        '**/wheel-*'
    ]
    
    # Special handling for docs directories - remove docs but preserve botocore/docs
    docs_patterns = [
        '**/docs'
    ]
    
    # for pattern in cleanup_patterns:
    #     for path in Path(build_dir).glob(pattern):
    #         if path.is_dir():
    #             shutil.rmtree(path, ignore_errors=True)
    #             print(f"  Removed directory: {path.relative_to(build_dir)}")
    #         elif path.is_file():
    #             path.unlink()
    #             print(f"  Removed file: {path.relative_to(build_dir)}")
    #
    # # Handle docs directories with special logic to preserve essential AWS SDK docs
    # for pattern in docs_patterns:
    #     for path in Path(build_dir).glob(pattern):
    #         if path.is_dir():
    #             # Check if this is botocore/docs, boto3/docs, or awscli/docs - preserve these
    #             path_str = str(path.relative_to(build_dir))
    #             if 'botocore/docs' in path_str or 'boto3/docs' in path_str or 'awscli/docs' in path_str:
    #                 print(f"  Preserved essential directory: {path.relative_to(build_dir)}")
    #             else:
    #                 shutil.rmtree(path, ignore_errors=True)
    #                 print(f"  Removed docs directory: {path.relative_to(build_dir)}")


def main():
    """Main deployment function."""
    print("="*60)
    print("AWS Lambda Deployment Script")
    print("="*60)
    
    # Get current directory
    current_dir = os.getcwd()
    print(f"Working directory: {current_dir}")
    
    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        print("Error: main.py not found. Please run this script from the api directory.")
        sys.exit(1)
    
    if not os.path.exists('Pipfile'):
        print("Error: Pipfile not found. Please run this script from the api directory.")
        sys.exit(1)
    
    # Create temporary build directory
    with tempfile.TemporaryDirectory() as temp_dir:
        build_dir = os.path.join(temp_dir, 'lambda_package')
        os.makedirs(build_dir)
        print(f"Build directory: {build_dir}")
        
        try:
            # Install dependencies
            install_dependencies(build_dir)
            
            # Copy application files
            copy_application_files(current_dir, build_dir)
            
            # Clean up unnecessary files
            clean_package_directory(build_dir)
            
            # Create deployment package
            output_file = os.path.join(current_dir, 'lambda_deployment_package.zip')
            
            # Remove existing package if it exists
            if os.path.exists(output_file):
                os.remove(output_file)
                print(f"Removed existing package: {output_file}")
            
            create_zip_package(build_dir, output_file)
            
            print("\n" + "="*60)
            print("DEPLOYMENT PACKAGE CREATED SUCCESSFULLY!")
            print("="*60)
            print(f"Package location: {output_file}")
            print(f"Package size: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
            print("\nNext steps:")
            print("1. Upload the zip file to AWS Lambda")
            print("2. Set the handler to: main.lambda_handler")
            print("3. Configure environment variables if needed")
            print("4. Set appropriate IAM permissions for Sagemaker access")
            
        except Exception as e:
            print(f"\nDeployment failed: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()