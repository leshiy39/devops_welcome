{{- define "welcome-page.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "welcome-page.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" (include "welcome-page.name" .) .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end }}
