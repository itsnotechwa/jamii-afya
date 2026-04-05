/**
 * upload.js
 * Handles the two-step S3 presigned-URL upload for medical bills.
 *
 * Step 1 – getPresignedUrl(fileName)  → back-end returns { url, fields? }
 * Step 2 – uploadFileToS3(url, file)  → PUT directly to S3 (no auth header)
 *
 * Returns the public S3 URL to attach to the claim payload as bill_url.
 */

import api from './axios';

/**
 * Request a presigned upload URL from the back-end.
 * The API currently returns HTTP 501 until S3 (or similar) is configured;
 * prefer attaching files via the emergency claim flow instead.
 * @param {string} fileName   e.g. "hospital_bill_2024.pdf"
 * @returns {Promise<{ url: string, fields?: Record<string,string> }>}
 */
export async function getPresignedUrl(fileName) {
  const { data } = await api.get('/api/upload/', { params: { fileName } });
  return data;
}

/**
 * PUT the file directly to S3 using the presigned URL.
 * Note: must NOT include the JWT Authorization header (S3 will reject it).
 * That's why we use native fetch rather than the api axios instance.
 *
 * @param {string} presignedUrl   URL returned by getPresignedUrl
 * @param {File}   file           Browser File object from <input type="file">
 * @param {function} [onProgress] Optional callback(percent: number)
 * @returns {Promise<string>}     The base S3 URL (strip query string from presignedUrl)
 */
export async function uploadFileToS3(presignedUrl, file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    if (onProgress) {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      });
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        // Strip query params to get the permanent S3 object URL
        const publicUrl = presignedUrl.split('?')[0];
        resolve(publicUrl);
      } else {
        reject(new Error(`S3 upload failed with status ${xhr.status}`));
      }
    };

    xhr.onerror = () => reject(new Error('S3 upload network error.'));

    xhr.open('PUT', presignedUrl);
    xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
    xhr.send(file);
  });
}

/**
 * Convenience: run both steps and return the final public bill URL.
 * Use this inside FormNewClaim.
 *
 * @param {File} file
 * @param {function} [onProgress]
 * @returns {Promise<string>}  Public S3 URL to store as bill_url on the claim
 */
export async function uploadBill(file, onProgress) {
  const { url } = await getPresignedUrl(file.name);
  const publicUrl = await uploadFileToS3(url, file, onProgress);
  return publicUrl;
}

/**
 * Fallback: if the back-end does not support presigned URLs,
 * convert the file to Base64 and POST it inline with the claim.
 * Wire this up in FormNewClaim by replacing uploadBill with uploadBillBase64.
 *
 * @param {File} file
 * @returns {Promise<string>}  data URI string (base64 encoded)
 */
export function uploadBillBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result); // data:application/pdf;base64,...
    reader.onerror = () => reject(new Error('File read failed.'));
    reader.readAsDataURL(file);
  });
}