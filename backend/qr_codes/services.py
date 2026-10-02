import io
import uuid
import qrcode
from django.conf import settings
from files.storage import StorageService

class QRGeneratorService:
    def __init__(self):
        self.storage_service = StorageService()

    def generate_qr(self, share_url: str) -> str:
        """
        Generates a QR code image buffer and uploads it to the storage backend.
        Returns the storage_key where the QR PNG is securely saved.
        """
        qr = qrcode.QRCode(
            version=None, # auto
            error_correction=qrcode.constants.ERROR_CORRECT_Q, # 25% error correction
            box_size=10,
            border=4,
        )
        qr.add_data(share_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Determine secure random storage key
        random_id = str(uuid.uuid4())
        storage_key = f"qr/{random_id}.png"
        
        img_data = buffer.getvalue()
        
        # We generate a presigned URL and do a direct HTTP PUT.
        # This completely bypasses botocore's forced 'aws-chunked' transfer encoding, 
        # which Storj explicitly rejects because it strictly requires a Content-Length header.
        upload_url = self.storage_service.generate_upload_url(storage_key, 'image/png')
        
        import requests
        try:
            response = requests.put(
                upload_url,
                data=img_data,
                headers={'Content-Type': 'image/png', 'Content-Length': str(len(img_data))},
                timeout=15
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to upload QR code: {str(e)}")
        
        return storage_key
