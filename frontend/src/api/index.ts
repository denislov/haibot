import axios from 'axios'


declare const BASE_URL: string;
declare const TOKEN: string;

const api = axios.create({
  baseURL: '/',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use(
  config => {
    const base = BASE_URL || "";
    const apiPrefix = "/api";
    const normalizedPath = config.url?.startsWith("/") ? config.url : `/${config.url}`;
    config.url = `${base}${apiPrefix}${normalizedPath}`;
    console.debug(config.url)
    return config
  }
)

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    return Promise.reject(new Error(String(msg)))
  },
)

export default api
