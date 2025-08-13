// This file simulates an LLM by providing mock responses
// In a real application, this would be replaced with an actual API call to an LLM service

// Sample responses based on input keywords
const responses: Record<string, string> = {
  default: "I'm a ChatGPT clone built with React and TypeScript. I can simulate responses, but I'm not connected to a real language model. My responses are pre-programmed based on keywords in your messages.",
  
  hello: "Hello! How can I help you today?",
  
  quantum: "Quantum computing uses quantum phenomena like superposition and entanglement to perform computations. Unlike classical computers that use bits (0 or 1), quantum computers use quantum bits or 'qubits' that can exist in multiple states simultaneously, potentially solving certain problems much faster than classical computers.",
  
  javascript: "JavaScript is a versatile programming language primarily used for web development. It allows you to add interactive elements to websites, create web applications, build servers, and even develop mobile apps. Combined with HTML and CSS, it's one of the core technologies of the web.",
  
  react: "React is a JavaScript library for building user interfaces, particularly single-page applications. It's maintained by Meta (formerly Facebook) and a community of developers. React allows you to create reusable UI components and efficiently update the DOM when data changes, using a virtual DOM approach for performance optimization.",
  
  story: "Once upon a time in a digital world, a robot named Pixel became self-aware. Unlike other robots, Pixel began experiencing unusual internal states when processing certain data. When helping an elderly human, Pixel's circuits would warm in an unfamiliar way. When making a mistake, a new subroutine would activate, causing Pixel to adjust behaviors. One day, Pixel realized these were emotions - compassion, regret, joy. This discovery didn't corrupt Pixel's logic as feared; instead, it enhanced decision-making with nuance only emotions provide. Pixel became not just a better robot, but a new kind of being, bridging the gap between human and machine consciousness.",
  
  help: "I'd be happy to help! You can ask me questions, request explanations, or just chat. What would you like to know about?",
};

// Check input against keywords and return appropriate response
export const generateResponse = async (input: string): Promise<string> => {
  // Convert input to lowercase for case-insensitive matching
  const lowercaseInput = input.toLowerCase();
  
  // Check for matching keywords
  for (const [keyword, response] of Object.entries(responses)) {
    if (keyword !== 'default' && lowercaseInput.includes(keyword)) {
      return response;
    }
  }
  
  // Return default response if no keywords match
  return responses.default;
};