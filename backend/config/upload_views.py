from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class PresignedUploadUnavailableView(APIView):
    """
    Placeholder for a future S3-compatible presigned URL flow.
    Clients should attach files via emergency create + upload_document instead.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                'detail': (
                    'Presigned object storage is not configured. '
                    'Attach files when creating an emergency request, or POST to '
                    '/api/emergencies/{id}/upload_document/.'
                ),
            },
            status=501,
        )
