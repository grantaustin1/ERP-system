import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API } from '@/App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Dumbbell, Eye, EyeOff } from 'lucide-react';
import ChangePasswordDialog from '@/components/ChangePasswordDialog';

export default function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: ''
  });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showChangePasswordDialog, setShowChangePasswordDialog] = useState(false);
  const [isFirstLogin, setIsFirstLogin] = useState(false);
  const [forgotPasswordMode, setForgotPasswordMode] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (forgotPasswordMode) {
        // Request password reset
        await axios.post(`${API}/auth/request-password-reset`, { email: formData.email });
        toast.success('Password reset link sent to your email');
        setForgotPasswordMode(false);
        setFormData({ email: '', password: '', full_name: '' });
      } else {
        const endpoint = isLogin ? '/auth/login' : '/auth/register';
        const response = await axios.post(`${API}${endpoint}`, formData);
        
        localStorage.setItem('token', response.data.access_token);
        
        // Check if user needs to change password
        if (response.data.first_login || response.data.must_change_password) {
          setIsFirstLogin(true);
          setShowChangePasswordDialog(true);
          toast.info('Please change your password to continue');
        } else {
          toast.success(isLogin ? 'Login successful!' : 'Registration successful!');
          navigate('/');
        }
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChangeSuccess = () => {
    toast.success('Password changed successfully!');
    navigate('/');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)' }}>
      <Card className="w-full max-w-md bg-slate-800/50 border-slate-700 backdrop-blur-lg" data-testid="login-card">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-r from-emerald-500 to-teal-600 flex items-center justify-center">
              <Dumbbell className="w-8 h-8 text-white" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-white">GymAccess Hub</CardTitle>
          <CardDescription className="text-slate-400">
            {isLogin ? 'Sign in to your account' : 'Create a new account'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && !forgotPasswordMode && (
              <div className="space-y-2">
                <Label htmlFor="full_name" className="text-slate-200">Full Name</Label>
                <Input
                  id="full_name"
                  data-testid="full-name-input"
                  placeholder="John Doe"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  required={!isLogin}
                  className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-400"
                />
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-200">Email</Label>
              <Input
                id="email"
                data-testid="email-input"
                type="email"
                placeholder="admin@gym.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-400"
              />
            </div>
            {!forgotPasswordMode && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-slate-200">Password</Label>
                  {isLogin && (
                    <button
                      type="button"
                      onClick={() => setForgotPasswordMode(true)}
                      className="text-xs text-emerald-400 hover:text-emerald-300"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="relative">
                  <Input
                    id="password"
                    data-testid="password-input"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    required
                    className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-400 pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            )}
            <Button
              type="submit"
              data-testid="submit-button"
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-semibold"
              disabled={loading}
            >
              {loading ? 'Please wait...' : forgotPasswordMode ? 'Send Reset Link' : isLogin ? 'Sign In' : 'Sign Up'}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => {
                if (forgotPasswordMode) {
                  setForgotPasswordMode(false);
                } else {
                  setIsLogin(!isLogin);
                }
                setFormData({ email: '', password: '', full_name: '' });
              }}
              className="text-sm text-emerald-400 hover:text-emerald-300 transition-colors"
              data-testid="toggle-auth-button"
            >
              {forgotPasswordMode ? 'Back to login' : isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
            </button>
          </div>
          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => navigate('/member-portal')}
              className="text-sm text-teal-400 hover:text-teal-300 transition-colors"
              data-testid="member-portal-link"
            >
              Member Portal →
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Change Password Dialog */}
      <ChangePasswordDialog
        open={showChangePasswordDialog}
        onOpenChange={setShowChangePasswordDialog}
        isFirstLogin={isFirstLogin}
        onSuccess={handlePasswordChangeSuccess}
      />
    </div>
  );
}