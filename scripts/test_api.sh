#!/usr/bin/env bash
set -euo pipefail

curl -X POST "http://localhost:8000/api/v1/nid/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "front_image=@sample_data/nid_front.png" \
  -F "back_image=@sample_data/nid_back.png"
