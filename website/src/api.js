/** API base URL. Override with VITE_API_BASE_URL in .env (see .env.example). */
export const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'https://mail.harishcriticalcareclasses.com';

export async function sendEmails(formData) {
  try {
    const response = await fetch(`${BASE_URL}/send-emails`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      if (response.status === 413) {
        throw new Error(
          'Upload too large: reduce banner image sizes or ask the server admin to increase nginx client_max_body_size.'
        );
      }
      let errorMessage = `Server error: ${response.status} ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.error) {
          errorMessage = errorData.error;
        } else if (Array.isArray(errorData.detail)) {
          // FastAPI 422 validation errors
          errorMessage = errorData.detail
            .map((d) => {
              const field = Array.isArray(d.loc) ? d.loc.slice(1).join('.') : '';
              return field ? `${field}: ${d.msg}` : d.msg;
            })
            .join('; ');
        } else if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        }
      } catch {
        const text = await response.text();
        errorMessage = text || errorMessage;
      }
      throw new Error(errorMessage);
    }

    return response;
  } catch (error) {
    if (error.name === 'TypeError' && /fetch|network|failed/i.test(error.message)) {
      throw new Error(
        'Could not reach the API (network or CORS). Check that your frontend domain is allowed on the server, and that nginx/backend are running.'
      );
    }
    throw error;
  }
}
