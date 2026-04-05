/**
 * hospitals.js
 * Fetches the list of registered hospitals for the NewClaim dropdown.
 *
 * Hospital shape: { id, name, location }
 */

import api from './axios';

function hospitalsFromResponse(data) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.results)) return data.results;
  return [];
}

/**
 * @returns {Promise<{ id: number, name: string, location: string }[]>}
 */
export async function getHospitals() {
  try {
    const { data } = await api.get('/api/hospitals/', {
      params: { page_size: 100 },
    });
    return hospitalsFromResponse(data);
  } catch(error) {
    // Log the error for debugging purposes
    console.warn('Failed to fetch hospitals from API, using fallback list:', error.message);
    
    // Fallback to hardcoded list if API call fails
    return [
      { id: 1, name: 'Kenyatta National Hospital', location: 'Nairobi' },
      { id: 2, name: 'Aga Khan Hospital', location: 'Nairobi' },
      { id: 3, name: 'Mater Misericordiae Hospital', location: 'Nairobi' },
      { id: 4, name: 'The Nairobi Hospital', location: 'Nairobi' },
      { id: 5, name: 'Coptic Hospital', location: 'Nairobi' },
      { id: 6, name: 'Gertrude\'s Children Hospital', location: 'Nairobi' },
      { id: 7, name: 'Karen Hospital', location: 'Nairobi' },
      { id: 8, name: 'MP Shah Hospital', location: 'Nairobi' },
      { id: 9, name: 'Nairobi Women\'s Hospital', location: 'Nairobi' },
      { id: 10, name: 'Mbagathi District Hospital', location: 'Nairobi' },
      { id: 11, name: 'Mathare National Teaching and Referral Hospital', location: 'Nairobi' },
      { id: 12, name: 'Pumwani Maternity Hospital', location: 'Nairobi' },
      { id: 13, name: 'National Spinal Injury Referral Hospital', location: 'Nairobi' },
      { id: 14, name: 'Mama Lucy Kibaki Hospital', location: 'Nairobi' },
      { id: 15, name: 'Avenue Hospital', location: 'Nairobi' },
      { id: 16, name: 'Metropolitan Hospital', location: 'Nairobi' }
    ];
  }
}
