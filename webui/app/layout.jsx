export const metadata = {
  title: 'MFI-Edge WebUI',
  description: 'Local desktop interface for MFI-Edge experiments',
}

import './globals.css'

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  )
}
