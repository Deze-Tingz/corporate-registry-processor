import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../stores/auth';

interface Props {
  children: React.ReactNode;
  requiredRole?: string;
}

const ROLE_HIERARCHY: Record<string, number> = {
  intake_clerk: 0,
  reviewer: 1,
  supervisor: 2,
  administrator: 3,
};

export default function ProtectedRoute({ children, requiredRole }: Props) {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user) {
    const userLevel = ROLE_HIERARCHY[user.role] ?? -1;
    const requiredLevel = ROLE_HIERARCHY[requiredRole] ?? 99;
    if (userLevel < requiredLevel) {
      return <Navigate to="/" replace />;
    }
  }

  return <>{children}</>;
}
