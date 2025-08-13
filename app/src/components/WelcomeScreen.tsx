import React from 'react';

const WelcomeScreen: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] text-center px-4">
      <h1 className="text-4xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-teal-600 bg-clip-text text-transparent">
        NITI For States Assistant
      </h1>
      <p className="text-center text-gray-700 dark:text-gray-300 mb-8 max-w-6xl whitespace-pre-line">
        I can help you navigate through best practices and policies across different states in India.
        {"\n"}
        Feel free to ask me questions about state initiatives, policies, and successful implementation stories.
      </p>
    </div>
  );
};

export default WelcomeScreen;