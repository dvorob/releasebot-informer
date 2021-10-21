---

{{ $conf := .Values.releasebot }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ $conf.name }}
  annotations:
    kubernetes.io/ingress.class: nginx # класс контроллера. В нашем случаe nginx
spec:
  rules:
  - host: {{ $conf.ingress.host }} # доменное имя
    http:
      paths:
      - path: {{ $conf.ingress.path }}
        pathType: {{ $conf.ingress.pathType }} # https://kubernetes.io/docs/concepts/services-networking/ingress/#path-types
        backend:
          service: # указываем на какой сервис ingress должен пересылать трафик
            name: {{ $conf.name }}
            port:
              number: 80