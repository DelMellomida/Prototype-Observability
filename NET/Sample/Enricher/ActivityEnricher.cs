using Serilog.Core;
using Serilog.Events;
using System.Diagnostics;

namespace Sample.Enricher
{
    public class ActivityEnricher : ILogEventEnricher
    {
        public void Enrich(LogEvent logEvent, ILogEventPropertyFactory propertyFactory)
        {
            var activity = Activity.Current;

            if (activity != null)
            {
                var traceId = activity.TraceId.ToString();
                var spanId = activity.SpanId.ToString();
                var parentSpanId = activity.ParentSpanId.ToString();

                // Keep existing PascalCase properties for backward compatibility
                logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("TraceId", traceId));
                logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("SpanId", spanId));
                logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("ParentSpanId", parentSpanId));

                // Add snake_case properties required by backend
                logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("trace_id", traceId));
                logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("span_id", spanId));
                logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("parent_span_id", parentSpanId));
            }
        }
    }
}
