import './globals.css'

export const metadata = {
  title: 'Music Text Generator',
  description: 'Isola la voce da un brano e genera testo dai suoni vocali',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="it">
      <body>{children}</body>
    </html>
  )
}

