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
      - path: {{ . }}
        pathType: {{ $conf.ingress.pathType }} # https://kubernetes.io/docs/concepts/services-networking/ingress/#path-types
        backend:
          serviceName: {{ include "releasebot.fullname" . }}
          servicePort: {{ $conf.service_port }}