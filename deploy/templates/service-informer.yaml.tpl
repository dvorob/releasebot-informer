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
    protocol: TCP
    targetPort: {{ $conf.target_port }}
  - name: http
    port: 8080
    targetPort: {{ $conf.target_port }}
  selector:
    app: {{ $conf.name }}
  type: LoadBalancer
  loadBalancerIP: 10.250.16.100
