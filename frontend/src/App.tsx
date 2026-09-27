import { createBrowserRouter, RouterProvider } from 'react-router'
import { Layout } from '@/components/layout'
import { RequireHost } from '@/components/require-host'
import { DashboardPage } from '@/pages/dashboard-page'
import { LandingPage } from '@/pages/landing-page'
import { LogInPage } from '@/pages/log-in-page'
import { NotFoundPage } from '@/pages/not-found-page'
import { SignUpPage } from '@/pages/sign-up-page'

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <LandingPage /> },
      { path: '/signup', element: <SignUpPage /> },
      { path: '/login', element: <LogInPage /> },
      {
        element: <RequireHost />,
        children: [{ path: '/dashboard', element: <DashboardPage /> }],
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

function App() {
  return <RouterProvider router={router} />
}

export default App
