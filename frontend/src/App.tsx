import { createBrowserRouter, RouterProvider } from 'react-router'
import { Layout } from '@/components/layout'
import { LandingPage } from '@/pages/landing-page'
import { NotFoundPage } from '@/pages/not-found-page'

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <LandingPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

function App() {
  return <RouterProvider router={router} />
}

export default App
