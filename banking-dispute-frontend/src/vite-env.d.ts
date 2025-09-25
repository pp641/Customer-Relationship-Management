/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_REACT_APP_API_URL : string
    readonly VITE_REACT_APP_WS_URL : string
    readonly VITE_REACT_APP_ENVIRONMENT : string
    readonly VITE_REACT_APP_VERSION : string
  }
  
  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
  