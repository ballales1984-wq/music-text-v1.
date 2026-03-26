import './globals.css'
import Script from 'next/script'

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
      <head>
        <Script
          async
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2145959534306055"
          crossOrigin="anonymous"
          strategy="afterInteractive"
        />
      </head>
      <body>{children}</body>
    </html>
  )
}

