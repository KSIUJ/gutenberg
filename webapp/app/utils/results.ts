/**
 * This module is inspired by Rust's `Result` type.
 * The `Result` type defined here is a union of `ResultOk` and `ResultError`.
 * Using a returned Result instead of throwing an exception makes it easier to handle multiple
 * errors and guarantees type safety.
 */

export type ResultOk<T> = {
  errors: null;
  value: T;
};
export type ResultError<E> = {
  errors: E[];
  value: null;
};
export type Result<T, E> = ResultOk<T> | ResultError<E>;

export const ok = <T>(value: T): ResultOk<T> => ({
  errors: null,
  value,
});

export const error = <E>(...errors: E[]): ResultError<E> => ({
  errors,
  value: null,
});

/*
    *-------------------------------------*
    | Abandon all hope, ye who enter here |
    *-------------------------------------*
*/

export type CollectedValues<Input extends Record<string, unknown> | unknown[]> = {
  [K in keyof Input]: Input[K] extends Result<infer T, unknown> ? T : never;
};

export type CollectedArrayError<InputArray extends Result<unknown, unknown>[]>
  = InputArray extends Result<unknown, infer E>[] ? E : never;

export type CollectedArrayResult<InputArray extends Result<unknown, unknown>[]>
  = Result<CollectedValues<InputArray>, CollectedArrayError<InputArray>>;

export type CollectedObjectError<InputObject extends Record<string, Result<unknown, unknown>>>
  = InputObject extends Record<string, Result<unknown, infer E>> ? E : never;

export type CollectedObjectResult<InputObject extends Record<string, Result<unknown, unknown>>>
  = Result<CollectedValues<InputObject>, CollectedObjectError<InputObject>>;

/**
 * Takes an array of results and returns a single result.
 * If any of the input results is an error, the returned result contains a merged array of all
 * encountered errors.
 * If all input results are ok, the `value` in the returned result is an array of all `value` fields
 * in the input list.
 *
 * @example
 * collectResultArray([
 *   ok(1),
 *   ok('foo'),
 *   ok(null),
 * ]);
 * // returns:
 * ok([1, 'foo', null]);
 *
 * @example
 * collectResultArray([
 *   ok(1),
 *   error('foo'),
 *   error('bar', 'baz'),
 * ]);
 * // returns:
 * error('foo', 'bar', 'baz');
 */
export const collectResultArray = <
  InputArray extends Result<unknown, unknown>[],
>(
  results: InputArray,
): CollectedArrayResult<InputArray> => {
  // The result is ok until any error is found
  let collectResult: Result<unknown[], unknown> = {
    errors: null,
    value: [],
  };
  results.forEach((result) => {
    if (result.errors !== null) {
      if (collectResult.errors === null) collectResult = {
        errors: [],
        value: null,
      };
      collectResult.errors.push(...result.errors);
    } else if (collectResult.errors === null) {
      collectResult.value.push(result.value);
    }
  });

  // In this case the code author is more confident than the compiler
  // (this does not necessarily mean that the code author is correct)
  return collectResult as CollectedArrayResult<InputArray>;
};

/**
 * Takes a record (object) of results and returns a single result with a record of all `value` fields.
 *
 * @example
 * collectResultsObject({
 *   first: ok(1),
 *   second: ok('foo'),
 *   third: ok(null),
 * });
 * // returns:
 * ok({
 *   first: 1,
 *   second: 'foo',
 *   third: null,
 * });
 *
 * @example
 * collectResultArray({
 *   first: ok(1),
 *   second: error('foo'),
 *   third: error('bar', 'baz'),
 * });
 * // returns:
 * error('foo', 'bar', 'baz');
 */
export const collectResultsObject = <
  InputObject extends Record<string, Result<unknown, unknown>>,
>(
  results: InputObject,
): CollectedObjectResult<InputObject> => {
  const listOfResultsWithEntries: Result<[string, unknown], unknown>[] = Object.entries(results)
    .map(
      ([key, result]) => {
        if (result.errors !== null) return error(...result.errors);
        return ok([key, result.value]);
      },
    );
  const resultWithListOfEntries: Result<[string, unknown][], unknown> = collectResultArray(listOfResultsWithEntries);

  // In this case the code author is more confident than the compiler
  // (this does not necessarily mean that the code author is correct)
  if (resultWithListOfEntries.errors !== null) {
    // The type of `value` can be ignored, as it is null in this case.
    return resultWithListOfEntries as ResultError<CollectedObjectError<InputObject>>;
  }
  return ok(Object.fromEntries(resultWithListOfEntries.value) as CollectedValues<InputObject>);
};
