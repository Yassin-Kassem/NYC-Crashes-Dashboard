"""
Compress CSV files using gzip for efficient GitHub storage
Run this locally before committing
"""

import pandas as pd
import os

print("=" * 60)
print("COMPRESSING CSV FILES FOR DEPLOYMENT")
print("=" * 60)

# Compress crash data
print("\n📦 Compressing crash data...")
crash_file = "data/cleaned_collisions_crash_level.csv"
crash_gz = "data/cleaned_collisions_crash_level.csv.gz"

if os.path.exists(crash_file):
    # Read and write with gzip compression
    df_crash = pd.read_csv(crash_file, low_memory=False)
    df_crash.to_csv(crash_gz, index=False, compression='gzip')
    
    original_size = os.path.getsize(crash_file) / (1024 * 1024)  # MB
    compressed_size = os.path.getsize(crash_gz) / (1024 * 1024)  # MB
    ratio = (1 - compressed_size / original_size) * 100
    
    print(f"✅ {crash_file}")
    print(f"   Original: {original_size:.1f} MB")
    print(f"   Compressed: {compressed_size:.1f} MB")
    print(f"   Saved: {ratio:.1f}%")
else:
    print(f"❌ {crash_file} not found!")

# Compress person data
print("\n📦 Compressing person data...")
person_file = "data/cleaned_collisions_person_level.csv"
person_gz = "data/cleaned_collisions_person_level.csv.gz"

if os.path.exists(person_file):
    df_person = pd.read_csv(person_file, low_memory=False)
    df_person.to_csv(person_gz, index=False, compression='gzip')
    
    original_size = os.path.getsize(person_file) / (1024 * 1024)  # MB
    compressed_size = os.path.getsize(person_gz) / (1024 * 1024)  # MB
    ratio = (1 - compressed_size / original_size) * 100
    
    print(f"✅ {person_file}")
    print(f"   Original: {original_size:.1f} MB")
    print(f"   Compressed: {compressed_size:.1f} MB")
    print(f"   Saved: {ratio:.1f}%")
else:
    print(f"❌ {person_file} not found!")

print("\n" + "=" * 60)
print("NEXT STEPS:")
print("=" * 60)

# Check if files are small enough for GitHub
total_compressed = 0
if os.path.exists(crash_gz):
    total_compressed += os.path.getsize(crash_gz) / (1024 * 1024)
if os.path.exists(person_gz):
    total_compressed += os.path.getsize(person_gz) / (1024 * 1024)

print(f"\nTotal compressed size: {total_compressed:.1f} MB")

if total_compressed < 100:
    print("\n✅ Files are small enough for GitHub!")
    print("\n1. Add compressed files to Git:")
    print("   git add data/*.csv.gz")
    print("   git commit -m 'Add compressed data files'")
    print("   git push")
    print("\n2. Deploy to Render (no env variables needed)")
elif total_compressed < 500:
    print("\n⚠️  Files are large but manageable for GitHub")
    print("   Consider using Git LFS (Large File Storage)")
    print("\n   Or use GitHub Releases:")
    print("   1. Create a release: git tag v1.0 && git push origin v1.0")
    print("   2. Upload .csv.gz files to the release")
    print("   3. Set environment variables on Render with release URLs")
else:
    print("\n❌ Files too large for GitHub (>500MB)")
    print("   Use one of these options:")
    print("   1. Use only sampled data (run create_sampled_data.py)")
    print("   2. Upload to Dropbox/Google Drive and use URLs")
    print("   3. Use a cloud storage service (S3, etc.)")

print("\n" + "=" * 60)
