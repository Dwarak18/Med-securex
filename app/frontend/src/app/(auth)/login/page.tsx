'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/auth/useAuth';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Eye, EyeOff } from 'lucide-react';
import type { Role } from '@/types';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { useToast } from '@/hooks/use-toast';
import { signInWithEmailAndPassword, sendPasswordResetEmail } from 'firebase/auth';
import { auth, setAuthPersistence } from '@/lib/firebase';

const formSchema = z.object({
  email: z.string().email({ message: "Please enter a valid email." }),
  password: z.string().min(1, { message: "Password is required." }),
  rememberMe: z.boolean().default(false),
});

export default function LoginPage() {
  const [selectedRole, setSelectedRole] = useState<Role>('Analyst');
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();
  const { setUser, setRole } = useAuth();
  const { toast } = useToast();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { email: "", password: "", rememberMe: false },
  });

  const handleLogin = async (values: z.infer<typeof formSchema>) => {
    try {
      await setAuthPersistence(values.rememberMe);
      const userCredential = await signInWithEmailAndPassword(auth, values.email, values.password);
      const authUser = userCredential.user;
      const appUser = {
        uid: authUser.uid,
        name: authUser.displayName || 'User',
        email: authUser.email || '',
        avatarUrl: authUser.photoURL || `https://i.pravatar.cc/150?u=${authUser.uid}`,
        role: selectedRole,
      };
      setUser(appUser);
      setRole(selectedRole);
      localStorage.setItem('medi-secure-x2-user', JSON.stringify(appUser));
      router.push('/dashboard');
    } catch (error: any) {
      toast({ variant: "destructive", title: "Login Failed", description: error.message });
    }
  };

  const handlePasswordReset = async () => {
    const email = form.getValues("email");
    if (!email) {
      toast({ variant: "destructive", title: "Password Reset", description: "Please enter your email address first." });
      return;
    }
    try {
      await sendPasswordResetEmail(auth, email);
      toast({ title: "Password Reset", description: "Password reset email sent. Please check your inbox." });
    } catch (error: any) {
      toast({ variant: "destructive", title: "Error", description: error.message });
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md shadow-2xl rounded-2xl interactive-glow">
        <CardHeader className="text-center">
          <div className="flex flex-col justify-center items-center gap-2 mb-4">
            <Image src="/logo.png" alt="MedSecureX Shield" width={48} height={48} />
             <h1 className="text-4xl font-bold bg-gradient-to-r from-teal-400 via-blue-600 to-teal-400 bg-clip-text text-transparent">MedSecureX</h1>
          </div>
          <CardTitle className="sr-only">MedSecureX</CardTitle>
          <CardDescription>Sign in to access your security dashboard.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleLogin)} className="space-y-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input placeholder="name@example.com" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input type={showPassword ? 'text' : 'password'} placeholder="••••••••" {...field} />
                        <Button type="button" variant="ghost" size="icon" className="absolute right-1 top-1/2 h-7 w-7 -translate-y-1/2" onClick={() => setShowPassword(!showPassword)}>
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex items-center justify-between">
                <FormField
                    control={form.control}
                    name="rememberMe"
                    render={({ field }) => (
                        <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                            <FormControl>
                                <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                            </FormControl>
                            <div className="space-y-1 leading-none">
                                <FormLabel>Keep me logged in</FormLabel>
                            </div>
                        </FormItem>
                    )}
                />
                <Button type="button" variant="link" className="p-0 h-auto" onClick={handlePasswordReset}>
                  Forgot Password?
                </Button>
              </div>

              <div className="space-y-3 pt-2">
                <Label className="font-semibold">Select Your Role (for demo)</Label>
                <RadioGroup defaultValue="Analyst" value={selectedRole} onValueChange={(value: string) => setSelectedRole(value as Role)}>
                    <div className="flex items-center space-x-2">
                        <RadioGroupItem value="Viewer" id="r1" />
                        <Label htmlFor="r1">Viewer</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                        <RadioGroupItem value="Analyst" id="r2" />
                        <Label htmlFor="r2">Analyst</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                        <RadioGroupItem value="Admin" id="r3" />
                        <Label htmlFor="r3">Admin</Label>
                    </div>
                </RadioGroup>
              </div>

              <Button type="submit" className="w-full h-12 text-lg">
                Login
              </Button>
            </form>
          </Form>

          <p className="text-center text-sm text-muted-foreground">
            Don't have an account?{' '}
            <Link href="/signup" className="underline underline-offset-4 hover:text-primary">
              Sign Up
            </Link>
          </p>

        </CardContent>
      </Card>
    </main>
  );
}
