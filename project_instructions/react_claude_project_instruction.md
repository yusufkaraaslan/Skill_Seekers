# React Development Instructions

## When to Use This Skill

Use this instruction when working on:
- React components, hooks, and state management
- JSX syntax and component composition
- Modern React patterns (React 18+)
- Frontend UI development with React
- React performance optimization
- React testing and debugging

## Core Concepts

### 1. Component Patterns

**Functional Components (Preferred)**
```jsx
function UserProfile({ name, email, onUpdate }) {
  return (
    <div className="user-profile">
      <h2>{name}</h2>
      <p>{email}</p>
      <button onClick={onUpdate}>Update</button>
    </div>
  );
}
```

**Component with Children**
```jsx
function Card({ title, children }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      <div className="card-content">{children}</div>
    </div>
  );
}

// Usage
<Card title="Welcome">
  <p>This is the card content.</p>
</Card>
```

### 2. Hooks Reference

**useState - State Management**
```jsx
const [count, setCount] = useState(0);
const [user, setUser] = useState({ name: '', email: '' });

// Update object state (always create new object)
setUser(prev => ({ ...prev, name: 'New Name' }));
```

**useEffect - Side Effects**
```jsx
// Run on mount only
useEffect(() => {
  fetchData();
}, []);

// Run when dependency changes
useEffect(() => {
  document.title = `Count: ${count}`;
}, [count]);

// Cleanup function
useEffect(() => {
  const subscription = subscribe();
  return () => subscription.unsubscribe();
}, []);
```

**useContext - Context Consumption**
```jsx
const ThemeContext = createContext('light');

function ThemedButton() {
  const theme = useContext(ThemeContext);
  return <button className={theme}>Click me</button>;
}
```

**useRef - DOM References & Mutable Values**
```jsx
function TextInput() {
  const inputRef = useRef(null);

  const focusInput = () => {
    inputRef.current.focus();
  };

  return <input ref={inputRef} />;
}
```

**useMemo - Expensive Computations**
```jsx
const sortedItems = useMemo(() => {
  return items.sort((a, b) => a.name.localeCompare(b.name));
}, [items]);
```

**useCallback - Stable Function References**
```jsx
const handleClick = useCallback((id) => {
  setSelectedId(id);
}, []);
```

**useReducer - Complex State Logic**
```jsx
function reducer(state, action) {
  switch (action.type) {
    case 'increment':
      return { count: state.count + 1 };
    case 'decrement':
      return { count: state.count - 1 };
    default:
      throw new Error();
  }
}

const [state, dispatch] = useReducer(reducer, { count: 0 });
```

### 3. Custom Hooks

```jsx
// useFetch - Data fetching hook
function useFetch(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchData() {
      try {
        setLoading(true);
        const response = await fetch(url, { signal: controller.signal });
        const json = await response.json();
        setData(json);
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err);
        }
      } finally {
        setLoading(false);
      }
    }

    fetchData();
    return () => controller.abort();
  }, [url]);

  return { data, loading, error };
}

// useLocalStorage - Persistent state
function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(() => {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : initialValue;
  });

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value));
  }, [key, value]);

  return [value, setValue];
}

// useDebounce - Debounced value
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
```

### 4. Event Handling

```jsx
function Form() {
  const [value, setValue] = useState('');

  const handleChange = (e) => {
    setValue(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Submitted:', value);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input value={value} onChange={handleChange} />
      <button type="submit">Submit</button>
    </form>
  );
}
```

### 5. Conditional Rendering

```jsx
function UserGreeting({ isLoggedIn, user }) {
  // Early return pattern
  if (!isLoggedIn) {
    return <LoginButton />;
  }

  return (
    <div>
      {/* Ternary for inline conditionals */}
      <h1>{user.isAdmin ? 'Admin Dashboard' : 'User Dashboard'}</h1>

      {/* && for conditional display */}
      {user.notifications.length > 0 && (
        <NotificationBadge count={user.notifications.length} />
      )}

      {/* Nullish coalescing for defaults */}
      <p>Welcome, {user.displayName ?? user.email}</p>
    </div>
  );
}
```

### 6. Lists and Keys

```jsx
function ItemList({ items }) {
  return (
    <ul>
      {items.map((item) => (
        // Always use stable, unique keys (not array index)
        <li key={item.id}>
          <span>{item.name}</span>
          <span>${item.price}</span>
        </li>
      ))}
    </ul>
  );
}
```

### 7. Forms and Controlled Components

```jsx
function RegistrationForm() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.username) newErrors.username = 'Username required';
    if (!formData.email.includes('@')) newErrors.email = 'Valid email required';
    if (formData.password.length < 8) newErrors.password = 'Min 8 characters';
    return newErrors;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    // Submit form
    console.log('Form submitted:', formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        name="username"
        value={formData.username}
        onChange={handleChange}
        placeholder="Username"
      />
      {errors.username && <span className="error">{errors.username}</span>}

      <input
        name="email"
        type="email"
        value={formData.email}
        onChange={handleChange}
        placeholder="Email"
      />
      {errors.email && <span className="error">{errors.email}</span>}

      <input
        name="password"
        type="password"
        value={formData.password}
        onChange={handleChange}
        placeholder="Password"
      />
      {errors.password && <span className="error">{errors.password}</span>}

      <button type="submit">Register</button>
    </form>
  );
}
```

### 8. Context API for Global State

```jsx
// Create context
const AuthContext = createContext(null);

// Provider component
function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check authentication status on mount
    checkAuth().then(user => {
      setUser(user);
      setLoading(false);
    });
  }, []);

  const login = async (credentials) => {
    const user = await authService.login(credentials);
    setUser(user);
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  const value = { user, login, logout, loading };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook for consuming context
function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

// Usage in components
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) return <Spinner />;
  if (!user) return <Navigate to="/login" />;

  return children;
}
```

### 9. Error Boundaries

```jsx
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught:', error, errorInfo);
    // Log to error reporting service
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>Something went wrong</h2>
          <button onClick={() => this.setState({ hasError: false })}>
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Usage
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

### 10. React 18+ Features

**Automatic Batching**
```jsx
// All updates are batched automatically in React 18
function handleClick() {
  setCount(c => c + 1);
  setFlag(f => !f);
  // Only one re-render occurs
}
```

**Transitions**
```jsx
import { useTransition, startTransition } from 'react';

function SearchResults() {
  const [isPending, startTransition] = useTransition();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleChange = (e) => {
    setQuery(e.target.value);

    // Mark as low priority update
    startTransition(() => {
      setResults(filterResults(e.target.value));
    });
  };

  return (
    <div>
      <input value={query} onChange={handleChange} />
      {isPending ? <Spinner /> : <ResultsList results={results} />}
    </div>
  );
}
```

**Suspense for Data Fetching**
```jsx
import { Suspense } from 'react';

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <UserProfile />
    </Suspense>
  );
}
```

## Best Practices

### Do's ✅

1. **Use functional components and hooks** - Cleaner, more composable code
2. **Lift state up** - Share state between components through common parent
3. **Use TypeScript** - Type safety prevents bugs
4. **Memoize expensive operations** - useMemo, useCallback, React.memo
5. **Extract custom hooks** - Reuse stateful logic across components
6. **Use keys properly** - Stable, unique identifiers for list items
7. **Clean up effects** - Return cleanup function from useEffect
8. **Co-locate related code** - Keep component, styles, tests together

### Don'ts ❌

1. **Don't mutate state directly** - Always create new objects/arrays
2. **Don't use array index as key** - Causes issues with reordering
3. **Don't call hooks conditionally** - Breaks Rules of Hooks
4. **Don't overuse context** - Can cause unnecessary re-renders
5. **Don't forget dependency arrays** - Leads to stale closures
6. **Don't inline objects in JSX** - Creates new references each render

## Performance Optimization

```jsx
// Use React.memo for expensive pure components
const ExpensiveList = React.memo(function ExpensiveList({ items }) {
  return items.map(item => <ExpensiveItem key={item.id} {...item} />);
});

// Use virtualization for long lists
import { FixedSizeList } from 'react-window';

function VirtualizedList({ items }) {
  return (
    <FixedSizeList
      height={400}
      itemCount={items.length}
      itemSize={50}
    >
      {({ index, style }) => (
        <div style={style}>{items[index].name}</div>
      )}
    </FixedSizeList>
  );
}

// Code splitting with lazy loading
const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <HeavyComponent />
    </Suspense>
  );
}
```

## Testing Patterns

```jsx
// Component testing with React Testing Library
import { render, screen, fireEvent } from '@testing-library/react';

test('increments counter on click', () => {
  render(<Counter />);

  const button = screen.getByRole('button', { name: /increment/i });
  fireEvent.click(button);

  expect(screen.getByText(/count: 1/i)).toBeInTheDocument();
});

// Testing hooks
import { renderHook, act } from '@testing-library/react';

test('useCounter increments value', () => {
  const { result } = renderHook(() => useCounter());

  act(() => {
    result.current.increment();
  });

  expect(result.current.count).toBe(1);
});
```

## File Structure Recommendation

```
src/
├── components/           # Reusable UI components
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx
│   │   └── Button.module.css
│   └── ...
├── hooks/                # Custom hooks
│   ├── useFetch.ts
│   ├── useLocalStorage.ts
│   └── ...
├── context/              # React contexts
│   ├── AuthContext.tsx
│   └── ThemeContext.tsx
├── pages/                # Page components
│   ├── Home.tsx
│   └── Dashboard.tsx
├── services/             # API calls, external services
│   └── api.ts
├── utils/                # Helper functions
│   └── formatters.ts
└── types/                # TypeScript types
    └── index.ts
```

## Quick Reference

| Hook | Purpose | Common Use Case |
|------|---------|-----------------|
| useState | Local component state | Form inputs, toggles |
| useEffect | Side effects | API calls, subscriptions |
| useContext | Consume context | Theme, auth, i18n |
| useRef | DOM refs, mutable values | Focus, timers |
| useMemo | Memoize values | Expensive calculations |
| useCallback | Memoize functions | Event handlers for children |
| useReducer | Complex state logic | Forms, multi-step flows |
