comfy --skip-prompt --workspace=$NFS_VOLUME/ComfyUI install --nvidia
/usr/bin/python3 -m pip install -r /var/nfs-mount/comfyui-storage/ComfyUI/requirements.txt
pip3 install av
pip3 install -r /var/nfs-mount/comfyui-storage/ComfyUI/requirements.txt
pip3 install spaces 
python3 --version
mkdir -p "$NFS_VOLUME/workflows"
