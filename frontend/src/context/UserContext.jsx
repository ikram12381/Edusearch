import { createContext, useContext, useEffect, useState } from "react";
import { MOCK_USER } from "../services/mockData.js";

const UserContext = createContext(null);
const STORAGE_KEY = "edusearch:user";

export function UserProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) return { ...MOCK_USER, ...JSON.parse(stored) };
    } catch {
      // ignore malformed storage, fall back to defaults
    }
    return MOCK_USER;
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
  }, [user]);

  const updateUser = (updates) => setUser((prev) => ({ ...prev, ...updates }));

  return (
    <UserContext.Provider value={{ user, setUser, updateUser }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within a UserProvider");
  return ctx;
}
