---

{{ $conf := .Values.releasebot }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ $conf.name }}
  annotations:
    kubernetes.io/ingress.class: nginx
spec:
  rules:
  - host: {{ $conf.ingress.host }} # доменное имя
    http:
      paths:
      - path: {{ . }}
        pathType: {{ $conf.ingress.pathType }}
        backend:
          service:
            name: {{ include "releasebot.fullname" . }}
            port:
              number: {{ $conf.service_port }}
