'use client';

import { type ReactNode, createContext, useState, useEffect } from 'react';
import { type User as FirebaseAuthUser } from 'firebase/auth';
import { auth } from '@/lib/firebase';
import { type User, type Role } from '@/types';
import { Skeleton } from '../ui/skeleton';

interface AuthContextType {
  user: User | null;
  firebaseUser: FirebaseAuthUser | null;
  role: Role | null;
  loading: boolean;
  setRole: (role: Role | null) => void;
  setUser: (user: User | null) => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [firebaseUser, setFirebaseUser] = useState<FirebaseAuthUser | null>(null);
  const [role, setRole] = useState<Role | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged(auth_user => {
      setFirebaseUser(auth_user);
      if (auth_user) {
        // In a real app, you might fetch user profile from Firestore here
        const storedUser = localStorage.getItem('medi-secure-x2-user');
        if (storedUser) {
            const parsedUser: User = JSON.parse(storedUser);
            setUser(parsedUser);
            setRole(parsedUser.role);
        } else {
            // Create a default user object if none is stored
            const newUser: User = {
                uid: auth_user.uid,
                name: auth_user.displayName || 'New User',
                email: auth_user.email || '',
                avatarUrl: auth_user.photoURL || `https://i.pravatar.cc/150?u=${auth_user.uid}`,
                role: 'Viewer' // Default role
            };
            setUser(newUser);
            setRole(newUser.role);
            localStorage.setItem('medi-secure-x2-user', JSON.stringify(newUser));
        }

      } else {
        setUser(null);
        setRole(null);
        localStorage.removeItem('medi-secure-x2-user');
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);
  
  const value = { user, firebaseUser, role, loading, setRole, setUser };

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="flex flex-col items-center gap-4">
            <Skeleton className="h-12 w-12 rounded-full" />
            <div className="space-y-2">
                <Skeleton className="h-4 w-[250px]" />
                <Skeleton className="h-4 w-[200px]" />
            </div>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
