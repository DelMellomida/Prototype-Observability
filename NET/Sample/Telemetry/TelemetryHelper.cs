using System.Diagnostics;

namespace Sample.Telemetry
{
    public class TelemetryHelper : ITelemetryHelper
    {
        private readonly ActivitySource _activitySource;

        public TelemetryHelper(ActivitySource activitySource)
        {
            _activitySource = activitySource;
        }

        /// <summary>
        /// Start a business-level activity/span. Uses injected ActivitySource and returns the started Activity.
        /// The caller should dispose the returned Activity (e.g. using var activity = StartBusinessSpan(...)).
        /// Span name is prefixed with "business." to follow span-naming conventions.
        /// </summary>
        public Activity? StartBusinessSpan(string spanName, System.Collections.Generic.Dictionary<string, object>? attributes = null)
        {
            var activity = _activitySource.StartActivity($"business.{spanName}", ActivityKind.Internal);

            if (activity != null && attributes != null)
            {
                foreach (var kvp in attributes)
                {
                    activity.SetTag(kvp.Key, kvp.Value?.ToString());
                }
            }

            return activity;
        }
    }
}
