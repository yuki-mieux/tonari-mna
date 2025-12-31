/**
 * ダッシュボード画面
 */
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { projectApi, sessionApi } from '../lib/api';
import type { Project } from '../types/api';

export function Dashboard() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);

  // プロジェクト一覧を取得
  const fetchProjects = useCallback(async () => {
    try {
      const response = await projectApi.list({ limit: 50 });
      setProjects(response.projects);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // プロジェクト作成
  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;

    setIsCreating(true);
    try {
      const project = await projectApi.create({ name: newProjectName.trim() });
      setProjects((prev) => [project, ...prev]);
      setNewProjectName('');
      setShowCreateForm(false);
    } catch (error) {
      console.error('Failed to create project:', error);
    } finally {
      setIsCreating(false);
    }
  };

  // セッション開始
  const handleStartSession = async (projectId: string) => {
    try {
      const response = await sessionApi.create(projectId);
      navigate(`/session/${response.session_id}`);
    } catch (error) {
      console.error('Failed to start session:', error);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">プロジェクト一覧</h1>
          <p className="mt-1 text-sm text-gray-500">
            M&A案件のヒアリング・IM作成を管理します
          </p>
        </div>
        <Button onClick={() => setShowCreateForm(true)}>
          新規プロジェクト
        </Button>
      </div>

      {/* プロジェクト作成フォーム */}
      {showCreateForm && (
        <Card className="mb-6">
          <CardContent className="py-4">
            <div className="flex gap-4">
              <input
                type="text"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="プロジェクト名を入力..."
                className="flex-1 input"
                autoFocus
              />
              <Button
                onClick={handleCreateProject}
                isLoading={isCreating}
                disabled={!newProjectName.trim()}
              >
                作成
              </Button>
              <Button variant="secondary" onClick={() => setShowCreateForm(false)}>
                キャンセル
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* プロジェクトリスト */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full mx-auto" />
          <p className="mt-2 text-gray-500">読み込み中...</p>
        </div>
      ) : projects.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <svg
              className="w-16 h-16 mx-auto text-gray-300 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-1">
              プロジェクトがありません
            </h3>
            <p className="text-gray-500 mb-4">
              新規プロジェクトを作成して、M&Aヒアリングを開始しましょう
            </p>
            <Button onClick={() => setShowCreateForm(true)}>
              最初のプロジェクトを作成
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onStartSession={() => handleStartSession(project.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface ProjectCardProps {
  project: Project;
  onStartSession: () => void;
}

function ProjectCard({ project, onStartSession }: ProjectCardProps) {
  const statusLabels: Record<string, { label: string; variant: 'info' | 'success' | 'warning' }> = {
    active: { label: '進行中', variant: 'info' },
    completed: { label: '完了', variant: 'success' },
    archived: { label: 'アーカイブ', variant: 'warning' },
  };

  const status = statusLabels[project.status] || { label: project.status, variant: 'info' };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="truncate">{project.name}</CardTitle>
          <Badge variant={status.variant}>{status.label}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        {project.company_name && (
          <p className="text-sm text-gray-600 mb-2">{project.company_name}</p>
        )}
        <p className="text-xs text-gray-400 mb-4">
          更新: {new Date(project.updated_at).toLocaleDateString('ja-JP')}
        </p>
        <div className="flex gap-2">
          <Button size="sm" onClick={onStartSession}>
            ヒアリング開始
          </Button>
          <Button size="sm" variant="secondary">
            詳細
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
