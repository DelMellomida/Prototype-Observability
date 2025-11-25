using System.Diagnostics;

namespace Sample.Telemetry
{
    public interface ITelemetryHelper
    {
        Activity? StartBusinessSpan(string spanName, System.Collections.Generic.Dictionary<string, object>? attributes = null);
    }
}
