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
  - host: 'informer.intools.yooteam.ru'
    http:
      paths:
      - path: {{ $conf.ingress.path }}
        pathType: {{ $conf.ingress.pathType }}
        backend:
          service:
            name: 'informer'
            port:
              number: {{ $conf.service_port }}
