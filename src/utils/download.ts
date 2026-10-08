/**
 * Reliable Client-Side Blob Downloader
 * 
 * Bypasses iframe cookie check / proxy redirection by fetching data within
 * the authenticated application context and streaming it to the user's disk
 * via an in-memory Blob URL.
 */

/**
 * Download a Blob directly
 */
export const downloadBlob = (blob: Blob, filename: string): boolean => {
  try {
    const blobUrl = window.URL.createObjectURL(blob);
    const tempLink = document.createElement("a");
    tempLink.href = blobUrl;
    tempLink.download = filename;
    tempLink.style.display = "none";
    document.body.appendChild(tempLink);
    tempLink.click();

    setTimeout(() => {
      document.body.removeChild(tempLink);
      window.URL.revokeObjectURL(blobUrl);
    }, 400);

    return true;
  } catch (err) {
    console.error(`Error downloading blob ${filename}:`, err);
    return false;
  }
};

export const downloadFile = async (
  filename: string,
  mimeType: string,
  dataOrUrl: string | object | Blob,
  isUrl: boolean = false
): Promise<boolean> => {
  try {
    if (dataOrUrl instanceof Blob) {
      return downloadBlob(dataOrUrl, filename);
    }

    let payload = "";

    if (isUrl) {
      const res = await fetch(dataOrUrl as string);
      if (!res.ok) throw new Error(`Fetch failed with status ${res.status}`);
      payload = await res.text();
    } else if (typeof dataOrUrl === "object") {
      payload = JSON.stringify(dataOrUrl, null, 2);
    } else {
      payload = dataOrUrl as string;
    }

    if (!payload) {
      throw new Error("Empty payload for download");
    }

    const blob = new Blob([payload], { type: mimeType });
    const blobUrl = window.URL.createObjectURL(blob);
    const tempLink = document.createElement("a");
    tempLink.href = blobUrl;
    tempLink.download = filename;
    tempLink.style.display = "none";
    document.body.appendChild(tempLink);
    tempLink.click();

    setTimeout(() => {
      document.body.removeChild(tempLink);
      window.URL.revokeObjectURL(blobUrl);
    }, 400);

    return true;
  } catch (err) {
    console.error(`Error downloading ${filename}:`, err);
    return false;
  }
};
