---

{{ $conf := .Values.releasebot }}
apiVersion: v1
kind: Service
metadata:
  name: {{ $conf.name }}
spec:
  ports:
  - name: {{ $conf.name }}
    port: {{ $conf.service_port }}
    targetPort: {{ $conf.target_port }}
  selector:
    app: {{ $conf.name }}
  type: ClusterIP