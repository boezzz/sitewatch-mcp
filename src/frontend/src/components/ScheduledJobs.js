import React, { useState } from 'react';

const ScheduledJobs = ({ jobs, onToggleJob, onDeleteJob }) => {
  const [expandedJob, setExpandedJob] = useState(null);
  
  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  const toggleExpanded = (jobId) => {
    setExpandedJob(expandedJob === jobId ? null : jobId);
  };
  
  if (jobs.length === 0) {
    return (
      <div className="p-4">
        <div className="text-center text-gray-500">
          <svg className="mx-auto h-8 w-8 text-gray-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
          </svg>
          <p className="text-sm">No monitoring jobs yet</p>
          <p className="text-xs text-gray-400">Start a conversation to create one</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="overflow-y-auto h-full">
      {jobs.map((job) => (
        <div key={job.id} className="border-b border-gray-100">
          <div className="p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-2 ${job.is_active ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                  <h3 className="text-sm font-medium text-gray-900 truncate">
                    {job.name}
                  </h3>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Focus: {job.monitoring_focus}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Last run: {formatDate(job.last_run)}
                </p>
                {job.next_run && (
                  <p className="text-xs text-blue-600 mt-1">
                    Next run: {formatDate(job.next_run)}
                  </p>
                )}
              </div>
              
              <div className="flex items-center space-x-1 ml-2">
                <button
                  onClick={() => toggleExpanded(job.id)}
                  className="p-1 text-gray-400 hover:text-gray-600"
                >
                  <svg className={`w-4 h-4 transform ${expandedJob === job.id ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                
                <button
                  onClick={() => onToggleJob(job.id)}
                  className={`p-1 ${job.is_active ? 'text-green-600 hover:text-green-800' : 'text-gray-400 hover:text-gray-600'}`}
                  title={job.is_active ? 'Pause job' : 'Resume job'}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    {job.is_active ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1m-6-8h8a2 2 0 012 2v8a2 2 0 01-2 2H6a2 2 0 01-2-2V8a2 2 0 012-2z" />
                    )}
                  </svg>
                </button>
                
                <button
                  onClick={() => onDeleteJob(job.id)}
                  className="p-1 text-red-400 hover:text-red-600"
                  title="Delete job"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
            
            {expandedJob === job.id && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="space-y-2">
                  <div>
                    <p className="text-xs font-medium text-gray-700">Query:</p>
                    <p className="text-xs text-gray-600">{job.query}</p>
                  </div>
                  
                  <div>
                    <p className="text-xs font-medium text-gray-700">URLs ({job.urls.length}):</p>
                    <div className="max-h-20 overflow-y-auto">
                      {job.urls.map((url, index) => (
                        <a
                          key={index}
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block text-xs text-blue-600 hover:text-blue-800 truncate"
                        >
                          {url}
                        </a>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <p className="text-xs font-medium text-gray-700">Schedule:</p>
                    <p className="text-xs text-gray-600">{job.schedule_cron}</p>
                  </div>
                  
                  <div>
                    <p className="text-xs font-medium text-gray-700">Created:</p>
                    <p className="text-xs text-gray-600">{formatDate(job.created_at)}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ScheduledJobs; 