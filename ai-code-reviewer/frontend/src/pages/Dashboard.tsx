import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchRepos, type Repo } from "../api/client";

export default function Dashboard() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRepos()
      .then(setRepos)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">AI Code Reviewer</h1>
        <p className="text-gray-500 mt-1">
          Automated pull-request analysis powered by LLMs
        </p>
      </header>

      {loading ? (
        <p className="text-gray-400">Loading repositories…</p>
      ) : repos.length === 0 ? (
        <div className="rounded-2xl bg-white shadow p-8 text-center text-gray-400">
          <p className="text-lg font-medium">No repositories tracked yet.</p>
          <p className="text-sm mt-1">
            Install the GitHub webhook to start reviewing pull requests.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {repos.map((repo) => (
            <Link
              key={repo.id}
              to={`/repos/${encodeURIComponent(repo.full_name)}`}
              className="rounded-2xl bg-white shadow p-6 hover:shadow-md transition-shadow"
            >
              <p className="font-semibold text-gray-800 truncate">{repo.full_name}</p>
              <p className="text-xs text-gray-400 mt-1">
                Since {new Date(repo.installed_at).toLocaleDateString()}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
