/** API base URL. Override with VITE_API_BASE_URL in .env (see .env.example). */
export const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001';

export async function sendEmails(formData) {
  try {
    const response = await fetch(`${BASE_URL}/send-emails`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let errorMessage = `Server error: ${response.status} ${response.statusText}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || errorMessage;
      } catch {
        const text = await response.text();
        errorMessage = text || errorMessage;
      }
      throw new Error(errorMessage);
    }

    return response;
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error(
        'Network error: Unable to connect to the server. Please make sure the backend is running.'
      );
    }
    throw error;
  }
}
