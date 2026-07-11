'use client';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            AI Kubernetes Agent
          </h1>
          <p className="text-xl text-gray-600">
            Troubleshoot Kubernetes with AI
          </p>
        </div>

        {/* Main Card */}
        <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8">
          <div className="space-y-6">
            {/* Status Section */}
            <div className="border-b pb-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                System Status
              </h2>
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-gray-700">Ready</span>
              </div>
            </div>

            {/* Investigate Button */}
            <div className="pt-4">
              <button
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg transition duration-200 ease-in-out transform hover:scale-105"
              >
                Investigate Cluster
              </button>
            </div>

            {/* Features */}
            <div className="pt-6 border-t">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Capabilities
              </h3>
              <ul className="space-y-2 text-gray-700">
                <li>✓ Analyze Kubernetes failures</li>
                <li>✓ Identify root causes with AI</li>
                <li>✓ Suggest automated fixes</li>
                <li>✓ View investigation history</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-16">
          <p className="text-gray-600">
            API: {process.env.NEXT_PUBLIC_API_BASE_URL}
          </p>
        </div>
      </div>
    </main>
  );
}
