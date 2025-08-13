export const generateStreamingResponse = async (
  input: string,
  SelectedCollections: string[],
  onChunk: (chunk: string) => void,
  onError: (error: Error) => void
) => {
  try {
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text: input, collections: SelectedCollections }),
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No reader available');
    }

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      // Extract all SSE data lines and concatenate them as-is
      const lines = chunk.split('\n').filter(line => line.startsWith('data: '));
      for (const line of lines) {
        const content = line.slice(6); // Remove 'data: '
        if (content !== '') {
          onChunk(JSON.parse(content)); // Parse JSON to restore all whitespace/newlines
        }
      }
    }
  } catch (error) {
    onError(error instanceof Error ? error : new Error('Unknown error'));
  }
};