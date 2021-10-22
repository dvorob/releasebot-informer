---

{{ $conf := .Values.releasebot }}
apiVersion: v1
kind: Service
metadata:
  name: {{ $conf.app_name }}
spec:
  ports:
  - name: {{ $conf.app_name }}
    port: {{ $conf.service_port }}
    targetPort: {{ $conf.target_port }}
  selector:
    app: {{ $conf.name }}
  type: ClusterIP